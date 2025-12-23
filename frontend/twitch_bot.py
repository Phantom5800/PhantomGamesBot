from datetime import datetime, timedelta, timezone
import json
import os
import random
import re
import utils.events
from copy import deepcopy
from typing import Optional
from twitchio import PartialUser
from twitchio.http import Route
from twitchio.ext import commands, pubsub, routines
from twitchio.ext.eventsub.models import NotificationEvent
from twitchio.ext.eventsub.websocket import EventSubWSClient
from commands.slots import Slots, SlotsMode
from utils.utils import *
from utils.crowd_control import *

unix_epoch = datetime.strptime("1970-1-1 00:00:00.000000+0000", "%Y-%m-%d %H:%M:%S.%f%z")

class PhantomGamesBot(commands.Bot):
    def __init__(self, sharedResources):
        self.channel_list = os.environ['TWITCH_CHANNEL'].split(',')
        super().__init__(
            token=os.environ['TWITCH_OAUTH_TOKEN'],
            client_id=os.environ['TWITCH_CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX']
        )

        # event tracking
        self.esclient = {}

        # command handlers
        self.custom = sharedResources.customCommandHandler
        self.quotes = sharedResources.quoteHandler
        self.speedrun = sharedResources.srcHandler
        self.markov = sharedResources.markovHandler
        self.anilist = sharedResources.anilist
        self.youtube = sharedResources.youtube
        self.slots = Slots(SlotsMode.TWITCH)

        # custom timers
        self.timer_queue = {}
        self.current_timer_msg = {}
        self.messages_since_timer = {}
        self.timer_lines = {}
        self.auto_chat_msg = {}
        self.auto_chat_lines_mod = {}
        self.auto_chat_lines = {}

        for channel in self.channel_list:
            channel = channel.lower()
            self.timer_queue[channel] = []
            self.current_timer_msg[channel] = 0
            self.messages_since_timer[channel] = 0
            self.timer_lines[channel] = tryParseInt(os.environ['TIMER_CHAT_LINES'], 5)
            self.auto_chat_msg[channel] = 0
            try:
                self.auto_chat_lines_mod[channel] = tryParseInt(os.environ[f'AUTO_CHAT_LINES_MOD_{channel}'], 10)
                self.auto_chat_lines[channel] = tryParseInt(os.environ[f'AUTO_CHAT_LINES_MIN_{channel}'], 20) + random.randint(0, self.auto_chat_lines_mod[channel])
            except:
                self.auto_chat_lines_mod[channel] = 10
                self.auto_chat_lines[channel] = 20 + random.randint(0, self.auto_chat_lines_mod[channel])

        # markov
        self.markov_data_store = True
        self.markov_store_minlen = int(os.environ['MARKOV_STORE_MIN'])
        self.banned_words = []
        with open('./commands/resources/bannedwords.txt', 'r', encoding="utf-8") as banned_words:
            self.banned_words = banned_words.readlines()
            for i, word in enumerate(self.banned_words):
                self.banned_words[i] = word.strip()

        # data
        self.first_redeems = {}
        with open('./commands/resources/first.json', 'r', encoding="utf-8") as first_redeems:
            data = json.load(first_redeems)
            self.first_redeems = deepcopy(data)
        self.misgender_warnings = {}
        self.current_rng = 0
        with open('./commands/resources/rng.txt', 'r', encoding="utf-8") as rng_value:
            self.current_rng = tryParseInt(rng_value.readline())

        # giveaway
        self.giveaway_open = False
        self.giveaway_list = []

        # random message response
        self.bless_count = 0
        self.bless_sent = False
        self.last_misgender_user = ""
        self.load_user_warnings()

        # load relevant data
        self.load_timer_events()
        print("=======================================")
        print(f"Twitch: {os.environ['BOT_NICK']} is online!")

        # start message timer
        try:
            self.timer_update.start()
            self.automatic_chat.start()
            if int(os.environ.get("CC_ENABLE")) >= 1:
                self.periodic_cc_update.start()
        except RuntimeError:
            print("Timer is already running")

    def load_timer_events(self):
        for channel in self.channel_list:
            with open(f'./commands/resources/channels/{channel}/timer_events.txt', 'r', encoding="utf-8") as txt_file:
                lines = txt_file.readlines()
                for line in lines:
                    command = line.strip()
                    command_exists = self.custom.command_exists(command, channel) or self.commands.get(command[1:])
                    if command_exists and command not in self.timer_queue[channel]:
                        self.timer_queue[channel].append(command)
            print(f"Timer events loaded for {channel}: {self.timer_queue[channel]}")

    def save_timer_events(self):
        for channel in self.channel_list:
            with open(f'./commands/resources/channels/{channel}/timer_events.txt', 'w', encoding="utf-8") as txt_file:
                for event in self.timer_queue[channel]:
                    txt_file.write(f"{event}\n")

    def load_user_warnings(self):
        try:
            with open(f'./commands/resources/warnings.json', 'r', encoding="utf-8") as text_file:
                data = json.load(text_file)
                self.misgender_warnings = deepcopy(data)
        except:
            print("[ERROR] warnigs.json does not exist yet.")

    def save_user_warnings(self):
        with open(f'./commands/resources/warnings.json', 'w', encoding="utf-8") as text_file:
            text_file.write(json.dumps(self.misgender_warnings))

    #####################################################################################################
    # error handling
    #####################################################################################################
    async def event_ready(self):
        await self.join_channels(self.channel_list)

    async def event_error(self, error: Exception, data: Optional[str] = None):
        print(f"[ERROR] TwitchIO Exception: {error}")

    '''
    Runs when an "invalid command" is sent by a user.
    '''
    async def event_command_error(self, ctx: commands.Context, error: Exception):
        # ignore command errors that exist in the custom command set
        return
        # command is None??? idk, figure this out later
        # if self.custom.command_exists(ctx.command.name):
        #     return
        # super().event_command_error(ctx, error)

    async def event_token_expired(self):
        print("[ERROR] OAUTH token expired")
        return None

    #####################################################################################################
    # generic events
    #####################################################################################################
    async def event_channel_joined(self, channel):
        print(f"[Twitch] Joined channel: {channel.name}")

    async def event_channel_join_failure(self, channel: str):
        print(f"[ERROR] Failed to join \"{channel} for some reason, try again\"")

    '''
    Get a random supported color for announcements
    '''
    def random_announcement_color(self):
        colors = ["orange", "green", "purple", "blue"]
        return colors[random.randrange(len(colors))]

    async def post_chat_announcement(self, streamer, announcement: str):
        bot = self.create_user(int(self.user_id), self.nick)
        await streamer.chat_announcement(token=os.environ['TWITCH_OAUTH_TOKEN'], moderator_id=bot.id, message=announcement, color=self.random_announcement_color())

    '''
    Runs every time a message is sent in chat.
    '''
    async def event_message(self, message):
        # make sure the bot ignores itself
        if (message.author is not None and message.author.name.lower() == os.environ['BOT_NICK'].lower()) or message.author is None:
            return

        # get the context of the current message
        ctx = await self.get_context(message)

        # track chat messages that have been posted since the last timer fired
        self.messages_since_timer[message.channel.name.lower()] += 1
        self.auto_chat_msg[message.channel.name.lower()] += 1

        if message is not None: # this has come up before??
            # handle custom commands
            if message.content is not None and len(message.content) > 0:
                # if people are spamming bless emotes, jump in "randomly"
                if "Bless" in message.content or "Prayge" in message.content:
                    self.bless_count = self.bless_count + 1
                    if random.randint(1, self.bless_count) >= 2 and not self.bless_sent:
                        self.bless_sent = True
                        await ctx.send("phanto274Bless phanto274Bless phanto274Bless")
                else:
                    self.bless_count = 0
                    self.bless_sent = False

                misgender_pattern = r"(^|\s)?(he|him|his|sir)($|\s)"
                if re.search(misgender_pattern, message.content.lower()) is not None:
                    self.last_misgender_user = message.author.name

                # look for commands
                command = message.content.split()[0]
                response = self.custom.parse_custom_command(command, message.channel.name)
                if response is not None:
                    response = await replace_vars_twitch(response, ctx, message.channel)
                    if "/announce" in response:
                        response = response.replace("/announce", "/me")
                        # try to post as an announcement, if it fails, post it with /me
                        try:
                            announcement = response.replace("/me", "")
                            streamer = await message.channel.user()
                            await self.post_chat_announcement(streamer, announcement)
                        except:
                            await ctx.send(response)
                    else:
                        await ctx.send(response)
                else:
                    await super().event_message(message)

                    # save twitch messages that are not commands, links and meet a minimum length requirement
                    self_post = message.content.startswith(os.environ['BOT_PREFIX'])
                    if self_post:
                        return

                    length_req = len(set(message.content.split())) >= self.markov_store_minlen
                    if not length_req:
                        return

                    contains_link = "https://" in message.content
                    if contains_link:
                        return

                    # filter out a banned word list for the bot
                    contains_banned_word = False
                    for word in self.banned_words:
                        words = message.content.lower().split(' ')
                        if word in words:
                            contains_banned_word = True
                            break
                    if contains_banned_word:
                        print(f"[Markov Filter] Skipped adding message: {message.content} - {message.author.name}")
                    else:
                        with open(f"./commands/resources/markov/markov-{datetime.now().year}.txt", "a+", encoding="utf-8") as f:
                            try:
                                f.write(f"[{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')} {message.channel.name}: {message.author.name}] @ {message.content}\n")
                            except:
                                print(f"[ERROR] Failed to add string to markov: {message.content}")

    #####################################################################################################
    # custom commands
    #####################################################################################################
    '''
    Utility function for command parsing to break up segments of commands.
    '''
    def command_msg_breakout(self, message: str, expectedParts: int) -> str:
        if expectedParts == 2:
            pattern = r"([!]\w+) (.*)"
            matches = re.match(pattern, message)
            if matches is not None:
                return matches.groups()
        elif expectedParts == 3:
            pattern = r"([!]\w+) ([!@:;.]?\w+) (.*)"
            matches = re.match(pattern, message)
            if matches is not None:
                return matches.groups()
        else:
            debugPrint(f"[command_msg_breakout] Unexpected amount of command parts {expectedParts}")
        return None

    '''
    Get a list of all commands the bot responds to, excluding mod-only commands.
    '''
    @commands.command(aliases=["commands"])
    async def getcommands(self, ctx: commands.Context):
        default_commands = self.commands
        command_list = []
        for key in default_commands.keys():
            if "command" in key or "add" in key or "timer" in key or "set" in key or key == "so":
                continue
            if "sendcc" in key:
                continue
            if "quote" in key and key != "quote":
                continue
            command_list.append(f"!{key}")
        # cannot actually append the custom list because the message is too long
        #command_list.extend(self.custom.get_command_list())
        command_list.sort()
        await ctx.send(f"Built in commands: {command_list}. Custom commands: https://github.com/Phantom5800/PhantomGamesBot/blob/master/commands/resources/channels/{ctx.message.channel.name}/custom_commands.json")

    '''
    Add a custom command through twitch chat.
    '''
    @commands.command(aliases=["addcom"])
    async def addcommand(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None:
                # find the intended command name
                command = command_parts[1]
                # get the command response
                command_response = command_parts[2]
                # attempt to add the command
                command_added = self.custom.add_command(command, command_response, 0, ctx.message.channel.name)
                if command_added:
                    await ctx.send(f"{ctx.message.author.mention} Successfully added command [{command}] -> {command_response}")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] already exists.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")

    '''
    Add a custom command alias through twitch chat.
    '''
    @commands.command()
    async def addalias(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None:
                # find the intended command name
                command = command_parts[1]
                # get the command response
                command_response = command_parts[2]
                # attempt to add the command
                command_added = self.custom.add_alias(command, command_response, ctx.message.channel.name)
                if command_added:
                    await ctx.send(f"{ctx.message.author.mention} Successfully added alias [{command}] -> [{command_response}]")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] already exists or [{command_response}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")

    '''
    Set cooldown on a custom command through twitch chat.
    '''
    @commands.command()
    async def setcooldown(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None:
                command = command_parts[1]
                cooldown = tryParseInt(command_parts[2])
                command_edited = self.custom.set_cooldown(command, cooldown, ctx.message.channel.name)
                if command_edited:
                    await ctx.send(f"{ctx.message.author.mention} Cooldown for [{command}] = {cooldown} seconds.")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a cooldown!")

    '''
    Set the random response chance for a custom command through twitch chat.
    '''
    @commands.command()
    async def setrng(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None:
                command = command_parts[1]
                rng = tryParseInt(command_parts[2])
                command_edited = self.custom.set_rng_response(command, rng, ctx.message.channel.name)
                if command_edited:
                    await ctx.send(f"{ctx.message.author.mention} Response chance for [{command}] = {rng}%")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response chance!")

    '''
    Edit a custom command through twitch chat.
    '''
    @commands.command(aliases=["editcom"])
    async def editcommand(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None:
                command = command_parts[1]
                command_response = command_parts[2]
                command_edited = self.custom.edit_command(command, command_response, 0, ctx.message.channel.name)
                if command_edited:
                    await ctx.send(f"{ctx.message.author.mention} Edited command [{command}] -> {command_response}")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")

    '''
    Delete a custom command through twitch chat.
    '''
    @commands.command(aliases=["removecom", "delcom"])
    async def removecommand(self, ctx: commands.Context, command: str = ""):
        if ctx.message.author.is_mod:
            if len(command) > 0:
                command_removed = self.custom.remove_command(command, ctx.message.channel.name)
                if command_removed:
                    await ctx.send(f"{ctx.message.author.mention} Removed command [{command}]")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command!")

    #####################################################################################################
    # ad manager
    #####################################################################################################
    async def get_ad_schedule(self, streamer: PartialUser):
        streamer_id = streamer.id
        token = os.environ.get(f"TWITCH_CHANNEL_TOKEN_{streamer.name.lower()}")

        endpoint = Route("GET", "channels/ads", query=[("broadcaster_id", streamer_id)], token=token)

        data = await self._http.request(endpoint, paginate=False)
        return data[0]['next_ad_at']

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.channel)
    async def ad(self, ctx):
        streamer = await ctx.message.channel.user()
        next_ad = await self.get_ad_schedule(streamer)
        print(next_ad)

    #####################################################################################################
    # timer
    #####################################################################################################
    '''
    Force post next timer message.
    '''
    async def post_next_timer_message(self, channel):
        self.messages_since_timer[channel] = 0
        stream_channel = self.get_channel(channel)
        streamer = await stream_channel.user()

        command = self.timer_queue[channel][self.current_timer_msg[channel]]
        message = self.custom.get_command(command, channel)
        if message is None:
            if command == "!follow":
                msg = await self.get_goal_msg(streamer)
                await self.post_chat_announcement(streamer, msg)
            elif command == "!subgoal":
                msg = await self.get_subgoal_msg(streamer.name)
                await self.post_chat_announcement(streamer, msg)
            elif command == "!youtube":
                response = self.youtube.get_youtube_com_message(streamer.name)
                if len(response) > 0:
                    await self.post_chat_announcement(streamer, response)
            elif command == "!newvid":
                video = self.youtube.get_newest_youtube_video(streamer.name)
                if len(video) > 0:
                    await self.post_chat_announcement(streamer, f"Check out the most recent YouTube upload: {video}")
        else:
            if stream_channel is None:
                print(f"[ERROR] Timer cannot find channel '{channel}' to post in??")
            else:
                is_announcement = "/announce" in message
                message = message.replace("/announce", "") # remove /announce from commands

                # try to post as an announcement, if it fails, post it with /me
                try:
                    if is_announcement:
                        await self.post_chat_announcement(streamer, message)
                    else:
                        await stream_channel.send(message)
                except:
                    await stream_channel.send(message)
        self.current_timer_msg[channel] = (self.current_timer_msg[channel] + 1) % len(self.timer_queue[channel])

    '''
    Periodic routine to send timer based messages.
    '''
    @routines.routine(minutes=int(os.environ['TIMER_MINUTES']), wait_first=True)
    async def timer_update(self):
        # update sub count file
        streamer = await self.get_channel("phantom5800").user()
        await self.update_sub_counts(streamer, 0)
        
        # post automated messages in channels
        for channel in self.channel_list:
            # check for timer messages
            if self.messages_since_timer[channel] >= self.timer_lines[channel] and len(self.timer_queue[channel]) > 0:
                await self.post_next_timer_message(channel)

    @commands.command()
    async def postnexttimer(self, ctx: commands.Context):
        if ctx.message.author.is_broadcaster:
            await self.post_next_timer_message(ctx.message.channel.name.lower())

    @commands.command()
    async def addtimer(self, ctx: commands.Context, command: str = ""):
        if ctx.message.author.is_mod:
            channel = ctx.message.channel.name.lower()
            if len(command) > 0:
                if self.custom.command_exists(command, channel) or self.commands.get(command[1:]):
                    if command not in self.timer_queue[channel]:
                        self.timer_queue[channel].append(command)
                        await self.save_timer_events()
                        await ctx.send(f"{ctx.message.author.mention} Command [{command}] has been added as a timer")
                    else:
                        await ctx.send(f"{ctx.message.author.mention} Command [{command}] is already in the timer queue")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist")
            else:
                await ctx.send(f"{ctx.message.author.mention} Specify a command to add to the timer")

    @commands.command()
    async def removetimer(self, ctx: commands.Context, command: str = ""):
        if ctx.message.author.is_mod:
            channel = ctx.message.channel.name.lower()
            if len(command) > 0:
                if command in self.timer_queue[channel]:
                    self.timer_queue[channel].remove(command)
                    await self.save_timer_events()
                    await ctx.send(f"{ctx.message.author.mention} [{command}] has been removed from the timer")
            else:
                await ctx.send(f"{ctx.message.author.mention} Specify a command to remove from the timer")

    @commands.command(aliases=["timer", "timers"])
    async def timerevents(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            channel = ctx.message.channel.name.lower()
            await ctx.send(f"Current timer events: {self.timer_queue[channel]}")

    #####################################################################################################
    # quotes
    #####################################################################################################
    @commands.command()
    async def quote(self, ctx: commands.Context, quote_id: str = None):
        # if no lookup specific, give random
        if quote_id is None:
            await ctx.send(self.quotes.pick_random_quote(ctx.message.channel.name))
        else:
            try:
                # do id search first, positive indexes or negative indexes for reverse
                quote = int(quote_id)
                if quote >= 0:
                    response = self.quotes.pick_specific_quote(quote_id, ctx.message.channel.name)
                else:
                    count = self.quotes.num_quotes(ctx.message.channel.name)
                    response = self.quotes.pick_specific_quote(str(count + quote), ctx.message.channel.name)
            except:
                # try and look for a keyword
                response = self.quotes.find_quote_keyword(quote_id, ctx.message.channel.name)
            if response is not None:
                await ctx.send(response)

    @commands.command()
    async def addquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod or 'vip' in ctx.message.author.badges:
            command_parts = self.command_msg_breakout(ctx.message.content, 2)
            if command_parts is not None and len(command_parts) > 1:
                new_quote = command_parts[1]
                if len(new_quote) > 0:
                    game_name = await get_game_name_from_twitch_for_user(self, ctx.message.channel.name)
                    response = self.quotes.add_quote(new_quote, game_name, ctx.message.channel.name, ctx.message.author.name)
                    await ctx.send(response)
                else:
                    await ctx.send(f"{ctx.message.author.mention} where's the quote?")
            else:
                await ctx.send(f"{ctx.message.author.mention} where's the quote?")

    @commands.command()
    async def editquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content, 3)
            if command_parts is not None and tryParseInt(command_parts[1], -1) >= 0:
                quote_id = int(command_parts[1])
                quote = command_parts[2]
                response = self.quotes.edit_quote(quote_id, quote, ctx.message.channel.name)
                await ctx.send(response)

    @commands.command(aliases=["delquote"])
    async def removequote(self, ctx: commands.Context, quote_id: str = "-1"):
        if ctx.message.author.is_mod:
            if tryParseInt(quote_id, -1) >= 0:
                response = self.quotes.remove_quote(int(quote_id), ctx.message.channel.name)
                await ctx.send(response)

    @commands.command()
    async def howtoquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod or 'vip' in ctx.message.author.badges:
            await ctx.respond("!addquote \"quote text\" - user")
        else:
            await ctx.respond("Become a mod or vip")

    #####################################################################################################
    # speedrun.com
    #####################################################################################################
    '''
    Get the personal best time for a game/category on speedrun.com. This command does take a few seconds to respond while it performs a search.
    '''
    # @commands.command()
    # @commands.cooldown(1, 10, commands.Bucket.channel)
    # async def pb(self, ctx: commands.Context):
    #     if len(os.environ['SRC_USER']) > 0:
    #         category = ctx.message.content[3:].strip()
    #         game = await get_game_name_from_twitch_for_user(self, ctx.message.channel.name)
    #         response = self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
    #         await ctx.send(response)

    @commands.command()
    async def speed(self, ctx: commands.Context):
        name = ctx.message.content[len("!speed"):].strip()
        game = None
        if name is not None and len(name) > 0:
            if name.startswith("user:"):
                name = name[len("user:"):]
                game = self.speedrun.get_random_user_game(name)
                await ctx.send(content=f"Would be really cool if {name} would speedrun {game}!")
                return
            else:
                game = self.speedrun.get_random_category(name)
        else:
            game = self.speedrun.get_random_game()
        await ctx.send(f"{ctx.message.author.mention} You should try speedrunning {game}!")

    #####################################################################################################
    # anilist
    #####################################################################################################
    @commands.command()
    async def anime(self, ctx: commands.Context):
        anime = self.anilist.getRandomAnimeName()
        await ctx.send(f"{ctx.message.author.mention} You should try watching \"{anime}\"!")

    #####################################################################################################
    # youtube
    #####################################################################################################
    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.channel)
    async def youtube(self, ctx: commands.Context):
        response = self.youtube.get_youtube_com_message(ctx.message.channel.name)
        if len(response) > 0:
            streamer = await ctx.message.channel.user()
            await self.post_chat_announcement(streamer, response)

    @commands.command()
    async def newvid(self, ctx: commands.Context):
        video = self.youtube.get_most_recent_video(ctx.message.channel.name, use_playlist_api=True)
        if len(video) > 0:
            streamer = await ctx.message.channel.user()
            await self.post_chat_announcement(streamer, f"Check out the most recent YouTube upload: {video}")

    @commands.command()
    async def setyoutubechannel(self, ctx: commands.Context):
        if ctx.message.author.is_broadcaster:
            params = ctx.message.content[len("!setyoutubechannel"):].strip().split()
            if len(params) != 2:
                await ctx.send(f"{ctx.message.author.mention} !setyoutubechannel requires a YouTube username and channel_id")
                return
            self.youtube.set_youtube_channel_data(ctx.message.channel.name, params[0], params[1])
            await ctx.send(f"{ctx.message.author.mention} set YouTube channel username to '{params[0]}' and channel id to '{params[1]}'")

    @commands.command()
    async def setyoutubehandle(self, ctx: commands.Context):
        if ctx.message.author.is_broadcaster:
            params = ctx.message.content[len("!setyoutubehandle"):].strip().split()
            if len(params) != 1:
                await ctx.send(f"{ctx.message.author.mention} !setyoutubehandle requires a YouTube handle")
                return
            self.youtube.set_youtube_handle(ctx.message.channel.name, params[0])
            await ctx.send(f"{ctx.message.author.mention} set your YouTube handle to @{params[0]}")

    #####################################################################################################
    # chatting
    #####################################################################################################
    '''
    Post a randomly generated chat message, 60 second per-channel cooldown.
    '''
    @commands.command()
    @commands.cooldown(1, 60, commands.Bucket.channel)
    async def chat(self, ctx: commands.Context):
        response = self.markov.get_markov_string()
        await ctx.send(response)

    '''
    Periodically posts automatically generated messages to chat.
    '''
    @routines.routine(minutes=int(os.environ['AUTO_CHAT_MINUTES']), wait_first=True)
    async def automatic_chat(self):
        for channel in self.channel_list:
            if self.auto_chat_msg[channel] >= self.auto_chat_lines[channel]:
                self.auto_chat_msg[channel] = 0
                try:
                    self.auto_chat_lines[channel] = tryParseInt(os.environ[f'AUTO_CHAT_LINES_MIN_{channel}'], 20) + random.randint(0, self.auto_chat_lines_mod[channel])
                except:
                    self.auto_chat_lines[channel] = 20 + random.randint(0, self.auto_chat_lines_mod[channel])

                stream_channel = self.get_channel(channel)
                if stream_channel is None:
                    print(f"[ERROR] Timer cannot find channel '{channel}' to post in??")
                else:
                    message = self.markov.get_markov_string()
                    print(f"[{datetime.now()}] Generated Message in {channel}: {message}")
                    await stream_channel.send(message)

    #####################################################################################################
    # "fun commands"
    #####################################################################################################
    @commands.command()
    @commands.cooldown(1, 60, commands.Bucket.channel)
    async def clip(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        try:
            # try and make a clip using the person that used this command
            chatter = await ctx.message.author.user()
            clip = await streamer.create_clip(token_for=chatter) 
            await ctx.send(f"{ctx.message.author.mention} {clip.edit_url}")
        except Exception as e:
            print(e)
            await ctx.send(f"{ctx.message.author.mention} failed to create a clip")

    '''
    Attempt to get how long a user has been following the channel for.
    '''
    @commands.command()
    @commands.cooldown(1, 60, commands.Bucket.user)
    async def followage(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        try:
            twitch_user = await ctx.message.author.user()
            follow_event = await streamer.fetch_channel_followers(token=os.environ['TWITCH_OAUTH_TOKEN'], user_id=twitch_user.id)
        except Exception as e:
            print(e)
            await ctx.send(f"{ctx.message.author.mention} something went wrong, oops")
            return
        if follow_event is not None and len(follow_event) == 1:
            follow_event = follow_event[0]
            span = datetime.now(timezone.utc) - follow_event.followed_at

            hours, remainder = divmod(span.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            years, days = divmod(days, 365.25)

            duration_str = f"{int(years)} years, {int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
            await ctx.send(f"{ctx.message.author.mention} has been following for {duration_str}!")
        else:
            await ctx.send(f"{ctx.message.author.mention} is not even following phanto274Shrug")

    '''
    If a mod uses this command, the last user to have used he/him/his gets timed out for 1 minute for each warning after the third in addition to the response.
    '''
    @commands.command()
    async def pronouns(self, ctx: commands.Context):
        if self.last_misgender_user != "":
            # increment a count of how many times this user has been warned
            if self.last_misgender_user in self.misgender_warnings:
                self.misgender_warnings[self.last_misgender_user] += 1
            else:
                self.misgender_warnings[self.last_misgender_user] = 1
            self.save_user_warnings()

            if ctx.author.is_mod:
                chatter = await get_twitch_user(self, self.last_misgender_user)
                streamer = await get_twitch_user(self, ctx.message.channel.name)

                # provide a warning a handful of times first
                if self.misgender_warnings[self.last_misgender_user] <= 3:
                    try:
                        await streamer.user.warn_user(
                            moderator=self.user_id, 
                            user_id=chatter.user.id, 
                            reason=f"{ctx.message.channel.name} uses they/them pronouns and we request that you use them when referencing the streamer")
                    except Exception as e:
                        print(f"[ERROR] Unable to provide warning to {self.last_misgender_user} -- {e}")
                else:
                    # if it still happens after enough warnings, timeout
                    try:
                        await streamer.user.timeout_user(
                            token=os.environ['TWITCH_OAUTH_TOKEN'], 
                            moderator_id=self.user_id, 
                            user_id=chatter.user.id, 
                            duration=self.misgender_warnings[self.last_misgender_user] * 60, # 1 minute per warning
                            reason="pronouns")
                    except Exception as e:
                        print(f"[ERROR] Can't timeout {self.last_misgender_user} -- {e}")

        self.last_misgender_user = ""
        await ctx.send("They / Them")

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.user)
    async def slots(self, ctx: commands.Context):
        await ctx.send(self.slots.roll(ctx.message.author.mention))

    @commands.command()
    async def rng(self, ctx: commands.Context):
        if self.current_rng == 0:
            await ctx.send("Current RNG: Neutral")
        elif self.current_rng > 0:
            await ctx.send(f"Current RNG: Good ({self.current_rng})")
        elif self.current_rng < 0:
            await ctx.send(f"Current RNG: Bad ({self.current_rng * -1})")

    #####################################################################################################
    # conversions
    #####################################################################################################
    @commands.command()
    async def ftoc(self, ctx: commands.Context, farenheit: int):
        await ctx.send(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @commands.command()
    async def ctof(self, ctx: commands.Context, celcius: int):
        await ctx.send(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")

    @commands.command()
    async def mitokm(self, ctx: commands.Context, miles: str):
        try:
            miles_f = float(miles)
            await ctx.send(f"{miles}mi is about {round(miles_f * 1.609344, 2)}km")
        except:
            await ctx.send(f"{ctx.message.author.mention} please specify a number to convert")

    @commands.command()
    async def kmtomi(self, ctx: commands.Context, km: str):
        try:
            km_f = float(km)
            await ctx.send(f"{km}km is about {round(km_f / 1.609344, 2)}mi")
        except:
            await ctx.send(f"{ctx.message.author.mention} please specify a number to convert")

    #####################################################################################################
    # stream info
    #####################################################################################################
    '''
    Get information about the bot itself.
    '''
    @commands.command()
    @commands.cooldown(1, 5, commands.Bucket.channel)
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    '''
    Get the current game being played on twitch.
    '''
    @commands.command()
    @commands.cooldown(1, 5, commands.Bucket.channel)
    async def game(self, ctx: commands.Context):
        game_name = await get_game_name_from_twitch_for_user(self, ctx.message.channel.name)
        await ctx.send(game_name)

    '''
    Get the current title of the stream.
    '''
    @commands.command()
    @commands.cooldown(1, 5, commands.Bucket.channel)
    async def title(self, ctx: commands.Context):
        streamtitle = await get_stream_title_for_user(self, ctx.message.channel.name)
        await ctx.send(streamtitle)

    #####################################################################################################
    # goals
    #####################################################################################################
    async def get_goal_msg(self, streamer, follower: bool = True) -> str:
        token = os.environ.get(f'TWITCH_CHANNEL_TOKEN_{streamer.name.lower()}')
        generic_msg = "Be sure to follow the stream, every follower is greatly appreciated and there are no alerts for new followers, so don\'t worry about getting called out of lurk!"
        if token:
            goals = await streamer.fetch_goals(token=token)
            for goal in goals:
                if goal.type == 'follower' and follower:
                    if goal.current_amount >= goal.target_amount:
                        return f'We hit our follower goal of {goal.target_amount}! {generic_msg}'
                    else:
                        return f'We are at {goal.current_amount} / {goal.target_amount} followers towards our goal! {generic_msg}'
                elif 'subscription' in goal.type and not follower:
                    if goal.current_amount >= goal.target_amount:
                        return f'We hit our sub goal to {goal.description} and will be doing that soon!'
                    else:
                        return f'We are at {goal.current_amount} / {goal.target_amount} subs towards our goal to {goal.description}!'
        if follower:
            return generic_msg
        else:
            return None

    async def get_subscriber_count(self, streamer, plus_points: bool = False) -> int:
        token = os.environ.get(f'TWITCH_CHANNEL_TOKEN_{streamer.name.lower()}')
        if token:
            count = 0
            sub_list = await streamer.fetch_subscriptions(token=token)
            if plus_points:
                for sub in sub_list:
                    if sub.user.name.lower() == streamer.name.lower():
                        continue
                    if not sub.gift:
                        # tier 3's are worth 6, tier 1 and 2 are worth their tier level
                        if sub.tier == 3:
                            count += 3
                        count += sub.tier
                        # can't tell if prime but those aren't supposed to count
            else:
                count = len(sub_list) - 1
            return count
        return -1

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.channel)
    async def follow(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        message = await self.get_goal_msg(streamer)
        await self.post_chat_announcement(streamer, message)

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.channel)
    async def subgoal(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        msg = await self.get_goal_msg(streamer, follower=False)
        await self.post_chat_announcement(streamer, msg)

    #####################################################################################################
    # fun stuff
    #####################################################################################################
    @commands.command()
    async def first(self, ctx: commands.Context):
        username = ctx.message.author.name.lower()
        if username in self.first_redeems:
            await ctx.send(f"{ctx.message.author.mention} has been first {self.first_redeems[username]} times!")
        else:
            await ctx.send(f"{ctx.message.author.mention} has never been first phanto274D")

    @commands.command()
    async def notfirst(self, ctx: commands.Context):
        username = ctx.message.author.name.lower()
        count = self.first_redeems[username] if username in self.first_redeems else 0
        total = 0
        for user in self.first_redeems:
            total += self.first_redeems[user]
        await ctx.send(f"{ctx.message.author.mention} has not been first {total - count} times SadPag")

    @commands.command()
    async def sendcc(self, ctx: commands.Context, bits: int):
        if ctx.message.author.is_broadcaster:
            if int(os.environ.get("CC_ENABLE")) == 1:
                handle_generic_cc_bits(bits)
            elif int(os.environ.get("CC_ENABLE")) == 2:
                handle_pm64_cc_bits(bits)

    @commands.command()
    async def sendcc2(self, ctx: commands.Context, subs: int):
        if ctx.message.author.is_broadcaster:
            if int(os.environ.get("CC_ENABLE")) == 1:
                handle_generic_cc_subs(subs)
            elif int(os.environ.get("CC_ENABLE")) == 2:
                handle_pm64_cc_subs(subs)

    @routines.routine(seconds=int(os.environ.get("CC_UPDATE_SECONDS", 10)), wait_first=True)
    async def periodic_cc_update(self):
        interval = int(os.environ.get("CC_UPDATE_SECONDS", 10))
        handle_cc_periodic_update(interval)

    #####################################################################################################
    # eventsub
    #####################################################################################################
    async def setup_eventsub(self, channel: str):
        channel = channel.lower()
        channel_info = await get_twitch_user(self, channel)
        channel_id = channel_info.user.id

        try:
            channel_token = os.environ.get(f"TWITCH_CHANNEL_TOKEN_{channel}", None)
            # register all events that require channel access
            if channel_token:
                client_name = f"{channel}_channel"
                self.esclient[client_name] = EventSubWSClient(self)

                # stream events
                await self.esclient[client_name].subscribe_channel_cheers(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_points_redeemed(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_subscriptions(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_subscription_messages(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_subscription_gifts(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_prediction_begin(broadcaster=channel_id, token=channel_token)
                # await self.esclient[client_name].subscribe_channel_charity_donate(broadcaster=channel_id, token=channel_token)

                # mod actions
                await self.esclient[client_name].subscribe_channel_bans(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_unbans(broadcaster=channel_id, token=channel_token)
                # await self.esclient[client_name].subscribe_channel_unban_request_create(broadcaster=channel_id, moderator=channel_id, token=channel_token)
                # await self.esclient[client_name].subscribe_channel_unban_request_resolve(broadcaster=channel_id, moderator=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_suspicious_user_update(broadcaster=channel_id, moderator=channel_id, token=channel_token)

                # notifications
                # await self.esclient[client_name].subscribe_channel_ad_break_begin(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_hypetrain_begin(broadcaster=channel_id, token=channel_token)
                # await self.esclient[client_name].subscribe_channel_hypetrain_progress(broadcaster=channel_id, token=channel_token)
                await self.esclient[client_name].subscribe_channel_hypetrain_end(broadcaster=channel_id, token=channel_token)
        except Exception as e:
            print(f"[Eventsub Error] Error subscribing to events on {channel}({channel_id}) with channel token: {e}")

        try:
            mod_token = os.environ.get("TWITCH_OAUTH_TOKEN")
            client_name = f"{channel}_mod"
            self.esclient[client_name] = EventSubWSClient(self)
            # notifications
            # await self.esclient[client_name].subscribe_channel_ad_break_begin(broadcaster=channel_id, token=mod_token)
            # await self.esclient[client_name].subscribe_channel_hypetrain_begin(broadcaster=channel_id, token=mod_token)
            # await self.esclient[client_name].subscribe_channel_hypetrain_progress(broadcaster=channel_id, token=mod_token)
            # await self.esclient[client_name].subscribe_channel_hypetrain_end(broadcaster=channel_id, token=mod_token)
            await self.esclient[client_name].subscribe_channel_raid(to_broadcaster=channel_id, token=mod_token)
            await self.esclient[client_name].subscribe_channel_stream_start(broadcaster=channel_id, token=mod_token)
            await self.esclient[client_name].subscribe_channel_stream_end(broadcaster=channel_id, token=mod_token)
        except Exception as e:
            print(f"[Eventsub Error] Error subscribing to events on {channel}({channel_id}) with mod token: {e}")
        print(f"[Eventsub] Finished initializing for {channel}")

    #####################################################################################################
    # eventsub stream events
    #####################################################################################################
    '''
    Channel point redemption event
    '''
    async def event_eventsub_notification_channel_reward_redeem(self, event: NotificationEvent):
        rewardData = event.data
        print(f"[Eventsub {rewardData.redeemed_at}] {rewardData.user.name.lower()} redeemed {rewardData.reward.title}")

        # track first redemptions
        if "First" in rewardData.reward.title:
            username = rewardData.user.name.lower()
            if username in self.first_redeems:
                self.first_redeems[username] += 1
            else:
                self.first_redeems[username] = 1
            with open('./commands/resources/first.json', 'w', encoding="utf-8") as first_redeems:
                json_str = json.dumps(self.first_redeems, indent=2)
                first_redeems.write(json_str)
            print(f"{username} redeemed First {self.first_redeems[username]} times")

        # RNG tracking
        if "RNG" in rewardData.reward.title:
            if "Good" in rewardData.reward.title:
                self.current_rng += 1
            elif "Bad" in rewardData.reward.title:
                self.current_rng -= 1
            with open('./commands/resources/rng.txt', 'w', encoding="utf-8") as rng_value:
                rng_value.write(str(self.current_rng))

        # attempt to give the user VIP
        if "VIP" in rewardData.reward.title:
            streamer = rewardData.broadcaster
            for channel in self.connected_channels:
                if channel.name.lower() == streamer.name.lower():
                    try:
                        await streamer.add_channel_vip(os.environ.get(f"TWITCH_CHANNEL_TOKEN_{streamer.name.lower()}"), rewardData.user.id)
                        await channel.send(f"Congrats to {rewardData.user.name} for becoming a VIP!")
                    except:
                        await channel.send(f"{rewardData.user.name} was not able to automatically be assigned VIP, the streamer will try and get to this as soon as possible!")

    '''
    Bit cheer event
    '''
    async def event_eventsub_notification_cheer(self, event: NotificationEvent):
        cheerData = event.data
        if cheerData.is_anonymous:
            print(f"[Eventsub {datetime.now()}] Anonymous cheered {cheerData.bits} bits!")
        else:
            print(f"[Eventsub {datetime.now()}] {cheerData.user.name.lower()} cheered {cheerData.bits} bits!")

        # pass bit amounts to crowd control
        if int(os.environ.get("CC_ENABLE")) == 1:
            handle_generic_cc_bits(cheerData.bits)
        elif int(os.environ.get("CC_ENABLE")) == 2:
            handle_pm64_cc_bits(cheerData.bits)

        # record bit cheers
        with open('C:/StreamAssets/LatestCheer.txt', 'w', encoding="utf-8") as last_cheer:
            last_cheer.write(f"Last Cheer: {cheerData.bits} {cheerData.user.name}")

    async def update_sub_counts(self, broadcaster, tier):
        with open('C:/StreamAssets/SubCount.txt', 'w', encoding="utf-8") as sub_count:
            count = await self.get_subscriber_count(broadcaster)
            if count >= 99:
                sub_count.write("99+")
            else:
                sub_count.write(f"{count}")

    '''
    New sub event
    '''
    async def event_eventsub_notification_subscription(self, event: NotificationEvent):
        subData = event.data
        # update most recent sub for non gifts
        if not subData.is_gift:
            print(f"[Eventsub {datetime.now()}] {subData.user.name.lower()} subscribed at tier {subData.tier}")

            if int(os.environ.get("CC_ENABLE")) == 1:
                handle_generic_cc_subs(1, subData.tier)
            elif int(os.environ.get("CC_ENABLE")) == 2:
                handle_pm64_cc_subs(1, subData.tier)

            with open('C:/StreamAssets/LatestSub.txt', 'w', encoding="utf-8") as last_sub:
                last_sub.write(f"New Sub: {subData.user.name}")

        await self.update_sub_counts(subData.broadcaster, subData.tier)

    '''
    Resub event
    '''
    async def event_eventsub_notification_subscription_message(self, event: NotificationEvent):
        subData = event.data
        print(f"[Eventsub {datetime.now()}] {subData.user.name.lower()} subscribed at tier {subData.tier} for {subData.cumulative_months} months!")

        with open('C:/StreamAssets/LatestSub.txt', 'w', encoding="utf-8") as last_sub:
            last_sub.write(f"New Sub: {subData.user.name}")

        await self.update_sub_counts(subData.broadcaster, subData.tier)

    '''
    Gift sub event
    '''
    async def event_eventsub_notification_subscription_gift(self, event: NotificationEvent):
        subData = event.data
        if subData.is_anonymous:
            print(f"[Eventsub {datetime.now()}] Anonymous gifted {subData.total} tier {subData.tier} subs!")
        else:
            print(f"[Eventsub {datetime.now()}] {subData.user.name.lower()} gifted {subData.total} tier {subData.tier} subs!")

        # pass sub amounts to crowd control
        if int(os.environ.get("CC_ENABLE")) == 1:
            handle_generic_cc_subs(subData.total, subData.tier)
        elif int(os.environ.get("CC_ENABLE")) == 2:
            handle_pm64_cc_subs(subData.total, subData.tier)

    '''
    Precition
    '''
    async def event_eventsub_notification_prediction_begin(self, event: NotificationEvent):
        predData = event.data
        await self.post_chat_announcement(predData.broadcaster, f"Prediction has started! Win channel points by predicting at the top of chat: {predData.title}")

    '''
    Charity donate
    '''
    async def event_eventsub_notification_channel_charity_donate(self, event: NotificationEvent):
        donoData = event.data
        value = donoData.donation_value / 10 ** donoData.decimal_places
        print(f"[Eventsub {datetime.now()}] Charity donation: {donoData.user.name.lower()} donated {value:.2f} {donoData.donation_currency} to {donoData.charity_name}!")

    #####################################################################################################
    # eventsub notifications
    #####################################################################################################
    '''
    Ad play started
    '''
    async def event_eventsub_notification_channel_ad_break_begin(self, event: NotificationEvent):
        adData = event.data
        if event.is_automatic:
            print(f"[Eventsub {adData.broadcaster.name}] Automatic ad break of {adData.duration} seconds started at {adData.started_at}")
        else:
            print(f"[Eventsub {adData.broadcaster.name}] Manual ad break of {adData.duration} seconds started at {adData.started_at}")

    '''
    Hype Train start
    '''
    async def event_eventsub_notification_channel_hypetrain_begin(self, event: NotificationEvent):
        hypeData = event.data
        print(f"[Eventsub {datetime.now()}] Hype train started at {hypeData.started_at}")
        notif = "A Hype Train has started!"
        await utils.events.twitchevents.twitch_stream_event(hypeData.broadcaster.name, utils.events.TwitchEventType.HypeTrainStart, notif)

    '''
    Hype Train progress
    '''
    async def event_eventsub_notification_channel_hypetrain_progress(self, event: NotificationEvent):
        hypeData = event.data

    '''
    Hype Train ended
    '''
    async def event_eventsub_notification_channel_hypetrain_end(self, event: NotificationEvent):
        hypeData = event.data
        await utils.events.twitchevents.twitch_stream_event(hypeData.broadcaster.name, utils.events.TwitchEventType.HypeTrainEnd)
        print(f"[Eventsub {datetime.now()}] Hype train ended at {hypeData.ended_at} at level {hypeData.level}")

    '''
    Stream went live event
    '''
    async def event_eventsub_notification_stream_start(self, event: NotificationEvent):
        # set values for start of streams
        self.current_rng = 0

        # send out stream start event to listeners
        streamOnlineData = event.data
        print(f"[Eventsub {streamOnlineData.started_at}] Stream has started for {streamOnlineData.broadcaster.name}")
        streamtitle = await get_stream_title_for_user(self, streamOnlineData.broadcaster.name)
        game = await get_game_name_from_twitch_for_user(self, streamOnlineData.broadcaster.name)
        notif = f"{game} | {streamtitle}"
        await utils.events.twitchevents.twitch_stream_event(streamOnlineData.broadcaster.name, utils.events.TwitchEventType.GoLive, notif)

    '''
    Stream ended event
    '''
    async def event_eventsub_notification_stream_end(self, event: NotificationEvent):
        streamOfflineData = event.data
        print(f"[Eventsub {datetime.now()}] Stream has ended for {streamOfflineData.broadcaster.name}")
        await utils.events.twitchevents.twitch_stream_event(streamOfflineData.broadcaster.name, utils.events.TwitchEventType.EndStream)

    '''
    Raid event
    '''
    async def event_eventsub_notification_raid(self, event: NotificationEvent):
        raidData = event.data
        if raidData.viewer_count > 1: # filters out potential spam, rarely an issue, but it has come up before
            await raidData.reciever.shoutout(token=os.environ['TWITCH_OAUTH_TOKEN'], to_broadcaster_id=raidData.raider.id, moderator_id=self.user_id)
        print(f"[Eventsub {datetime.now()}] {raidData.raider.name} raided with {raidData.viewer_count} viewers")

    #####################################################################################################
    # eventsub mod events
    #####################################################################################################
    '''
    User banned
    '''
    async def event_eventsub_notification_ban(self, event: NotificationEvent):
        banData = event.data
        reason = banData.reason or "Unspecified reason"
        if banData.permanent:
            banString = f"❌ `{banData.user.name}` has been banned in **{banData.broadcaster.name}** by _{banData.moderator.name}_ for '{reason}'"
            await utils.events.twitchevents.twitch_log(banData.broadcaster.name, banString)
        else:
            seconds_from_epoch = int((banData.ends_at - unix_epoch).total_seconds())
            discord_timestamp = f"<t:{seconds_from_epoch}:R>"
            timeoutString = f"❌ `{banData.user.name}` has been timed out in **{banData.broadcaster.name}** by _{banData.moderator.name}_ until {discord_timestamp} for '{reason}'"
            await utils.events.twitchevents.twitch_log(banData.broadcaster.name, timeoutString)

    '''
    User unbanned
    '''
    async def event_eventsub_notification_unban(self, event: NotificationEvent):
        banData = event.data
        banString = f"✅ `{banData.user.name}` has been unbanned in **{banData.broadcaster.name}** by _{banData.moderator.name}_"
        await utils.events.twitchevents.twitch_log(banData.broadcaster.name, banString)

    '''
    Unban request made
    '''
    async def event_eventsub_notification_unban_request_create(self, event: NotificationEvent):
        banData = event.data
        seconds_from_epoch = int((banData.created_at - unix_epoch).total_seconds())
        discord_timestamp = f"<t:{seconds_from_epoch}:f>"
        banString = f"[{discord_timestamp}] '{banData.user.name}' has created an unban request: '{banData.text}'"
        await utils.events.twitchevents.twitch_log(banData.broadcaster.name, banString)

    '''
    Unban request resolved
    '''
    async def event_eventsub_notification_unban_request_resolve(self, event: NotificationEvent):
        banData = event.data
        moderator_name = banData.moderator.name if banData.moderator is not None else "unknown"
        banString = ""
        if banData.status == 'approved':
            banString = f"✅ '{banData.user.name}' has been unbanned in **{banData.broadcaster.name}** by **{moderator_name}** following their unban request: '{banData.text}'"
        elif banData.status == 'denied':
            banString = f"❌ '{banData.user.name}'\'s unban request has been denied in **{banData.broadcaster.name}** by **{moderator_name}**: '{banData.text}'"
        elif banData.status == 'canceled':
            banString = f"❌ '{banData.user.name}'\'s unban request has been canceled in **{banData.broadcaster.name}**: '{banData.text}'"
        await utils.events.twitchevents.twitch_log(banData.broadcaster.name, banString)

    '''
    Unban request resolved
    '''
    async def event_eventsub_notification_suspicious_user_update(self, event: NotificationEvent):
        susData = event.data
        susString = ""
        if susData.trust_status == 'active_monitoring':
            susString = f"❌ '{susData.user.name}' is marked as _monitored_ in **{susData.broadcaster.name}** by **{susData.moderator.name}**"
        elif susData.trust_status == 'restricted':
            susString = f"❌ '{susData.user.name}' is marked as _restricted_ in **{susData.broadcaster.name}** by **{susData.moderator.name}**"
        else:
            susString = f"✅ '{susData.user.name}' is marked as _not suspicious_ in **{susData.broadcaster.name}** by **{susData.moderator.name}**"
        await utils.events.twitchevents.twitch_log(susData.broadcaster.name, susString)

def run_twitch_bot(sharedResources) -> PhantomGamesBot:
    bot = PhantomGamesBot(sharedResources)
    bot.loop.create_task(bot.setup_eventsub("phantom5800"))
    bot.loop.create_task(bot.setup_eventsub("phantomgamesbot"))
    #bot.loop.create_task(bot.setup_eventsub("ravenfp"))
    return bot
