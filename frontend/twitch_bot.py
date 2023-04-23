from datetime import datetime, timezone
import json
import os
import random
import re
from copy import deepcopy
from typing import Optional
from twitchio import PartialUser
from twitchio.ext import commands, pubsub, routines
from commands.slots import Slots, SlotsMode
from utils.utils import *

class PhantomGamesBot(commands.Bot):
    def __init__(self, sharedResources):
        self.channel_list = os.environ['TWITCH_CHANNEL'].split(',')
        print(f"Joining twitch channels: {self.channel_list}")
        super().__init__(
            token=os.environ['TWITCH_OAUTH_TOKEN'],
            client_id=os.environ['TWITCH_CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
            initial_channels=self.channel_list
        )

        # subgoal tracker
        self.pubsub = {}
        self.subgoal_info = {}
        self.load_subgoal_data()
        for channel in self.channel_list:
            if self.subgoal_info[channel] is None:
                self.subgoal_info[channel] = {
                    "subs": [0] * 12,
                    "incentive": "",
                    "goal": 0
                }

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
        self.markov_store_minlen = 6
        self.banned_words = []
        with open('./commands/resources/bannedwords.txt', 'r', encoding="utf-8") as banned_words:
            self.banned_words = banned_words.readlines()
            for i, word in enumerate(self.banned_words):
                self.banned_words[i] = word.strip()

        # random message response
        self.bless_count = 0
        self.bless_sent = False

        # load relevant data
        self.load_timer_events()
        print("=======================================")
        print(f"Twitch: {os.environ['BOT_NICK']} is online!")

        # start message timer
        try:
            self.timer_update.start()
            self.automatic_chat.start()
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
                                f.write(f"{message.content}\n")
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
            if "command" in key or "timer" in key or "set" in key or key == "so":
                continue
            if "quote" in key and key != "quote":
                continue
            command_list.append(f"!{key}")
        # cannot actually append the custom list because the message is too long
        #command_list.extend(self.custom.get_command_list())
        command_list.sort()
        await ctx.send(f"Built in commands: {command_list}. Custom commands: https://github.com/Phantom5800/PhantomGamesBot/blob/master/commands/resources/custom_commands.json")

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
                msg = await self.get_follow_goal_msg(streamer)
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
                message = message.replace("/announce", "/me") # remove /announce from commands

                # try to post as an announcement, if it fails, post it with /me
                try:
                    announcement = message.replace("/me", "")
                    await self.post_chat_announcement(streamer, announcement)
                except:
                    await stream_channel.send(message)
        self.current_timer_msg[channel] = (self.current_timer_msg[channel] + 1) % len(self.timer_queue[channel])

    '''
    Periodic routine to send timer based messages.
    '''
    @routines.routine(minutes=int(os.environ['TIMER_MINUTES']), wait_first=True)
    async def timer_update(self):
        for channel in self.channel_list:
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
    async def quote(self, ctx: commands.Context, quote_id: str = "-1"):
        response = None

        if "latest" in quote_id.lower():
            await ctx.send(self.quotes.pick_specific_quote(str(self.quotes.num_quotes() - 1), ctx.message.channel.name))
            return

        quote = tryParseInt(quote_id, -1)
        if quote >= 0:
            response = self.quotes.pick_specific_quote(quote_id, ctx.message.channel.name)
        elif quote_id == "-1":
            response = self.quotes.pick_random_quote(ctx.message.channel.name)
        else:
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

    #####################################################################################################
    # speedrun.com
    #####################################################################################################
    '''
    Get the personal best time for a game/category on speedrun.com. This command does take a few seconds to respond while it performs a search.
    '''
    @commands.command()
    async def pb(self, ctx: commands.Context):
        if len(os.environ['SRC_USER']) > 0:
            category = ctx.message.content[3:].strip()
            game = await get_game_name_from_twitch_for_user(self, ctx.message.channel.name)
            response = self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
            await ctx.send(response)

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
    async def youtube(self, ctx: commands.Context):
        response = self.youtube.get_youtube_com_message(ctx.message.channel.name)
        if len(response) > 0:
            streamer = await ctx.message.channel.user()
            await self.post_chat_announcement(streamer, response)
    
    @commands.command()
    async def newvid(self, ctx: commands.Context):
        video = self.youtube.get_most_recent_video(ctx.message.channel.name)
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

    @commands.command()
    async def setyoutubesubgoal(self, ctx: commands.Context):
        if ctx.message.author.is_broadcaster:
            params = ctx.message.content[len("!setyoutubesubgoal"):].strip().split(" ", 1)
            if len(params) != 2:
                await ctx.send(f"{ctx.message.author.mention} !setyoutubegoal needs an integer goal and a message to be displayed. A goal of 0 will not show a sub goal in the !youtube command")
                return
            self.youtube.set_youtube_subgoal(ctx.message.channel.name, int(params[0]), params[1])
            await ctx.send(f"{ctx.message.author.mention} set the YouTube sub goal to: {int(params[0])}")

    #####################################################################################################
    # fun stream commands
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

    '''
    Attempt to get how long a user has been following the channel for.
    '''
    @commands.command()
    async def followage(self, ctx: commands.Context):
        streamer = await get_twitch_user(self, ctx.message.channel.name)
        try:
            twitch_user = await ctx.message.author.user()
            follow_event = await twitch_user.fetch_follow(to_user=streamer.user, token=os.environ['TWITCH_OAUTH_TOKEN'])
        except Exception as e:
            print(e)
            await ctx.send(f"{ctx.message.author.mention} something went wrong, oops")
            return
        if follow_event is not None:
            span = datetime.now(timezone.utc) - follow_event.followed_at

            hours, remainder = divmod(span.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            years, days = divmod(days, 365.25)

            duration_str = f"{int(years)} years, {int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
            await ctx.send(f"{ctx.message.author.mention} has been following for {duration_str}!")
        else:
            await ctx.send(f"{ctx.message.author.mention} is not even following phanto274Shrug")

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.user)
    async def slots(self, ctx: commands.Context):
        await ctx.send(self.slots.roll(ctx.message.author.mention))

    @commands.command()
    async def ftoc(self, ctx: commands.Context, farenheit: int):
        await ctx.send(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @commands.command()
    async def ctof(self, ctx: commands.Context, celcius: int):
        await ctx.send(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")
        
    #####################################################################################################
    # stream info
    #####################################################################################################
    '''
    Get information about the bot itself.
    '''
    @commands.command()
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    '''
    Get the current game being played on twitch.
    '''
    @commands.command()
    async def game(self, ctx: commands.Context):
        game_name = await get_game_name_from_twitch_for_user(self, ctx.message.channel.name)
        await ctx.send(game_name)

    '''
    Get the current title of the stream.
    '''
    @commands.command()
    async def title(self, ctx: commands.Context):
        streamtitle = await get_stream_title_for_user(self, ctx.message.channel.name)
        await ctx.send(streamtitle)

    '''
    Give a shoutout to a specific user in chat.
    '''
    @commands.command(aliases=["shoutout"])
    async def so(self, ctx: commands.Context, user: PartialUser = None):
        if ctx.message.author.is_mod and user is not None:
            game = await get_game_name_from_twitch_for_user(self, user.name)
            #await ctx.send(f"/shoutout {user.name}")
            await ctx.send(f"Checkout {user.name}, maybe drop them a follow! They were most recently playing {game} over at https://twitch.tv/{user.name}")

    #####################################################################################################
    # goals
    #####################################################################################################
    async def get_follow_goal_msg(self, streamer) -> str:
        token = os.environ.get(f'TWITCH_CHANNEL_TOKEN_{streamer.name.lower()}')
        generic_msg = "Be sure to follow the stream, every follower is greatly appreciated and there are no alerts for new followers, so don\'t worry about getting called out of lurk!"
        if token:
            goals = await streamer.fetch_goals(token=token)
            for goal in goals:
                if goal.type == 'follower':
                    if goal.current_amount >= goal.target_amount:
                        return f'We hit our follower goal to {goal.description} and will be doing that soon! {generic_msg}'
                    else:
                        return f'We are at {goal.current_amount} / {goal.target_amount} followers towards our goal to {goal.description}! {generic_msg}'
        return generic_msg

    @commands.command()
    async def follow(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        message = await self.get_follow_goal_msg(streamer)
        await self.post_chat_announcement(streamer, message)

    def load_subgoal_data(self):
        with open(f'./commands/resources/subgoals.json', 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
            self.subgoal_info = deepcopy(data)

    def save_subgoal_data(self):
        with open(f'./commands/resources/subgoals.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.subgoal_info, indent=2)
            json_file.write(json_str)

    async def get_subgoal_msg(self, channel: str) -> str:
        channel = channel.lower()
        now = datetime.now()
        goal = self.subgoal_info[channel]["goal"]
        current = self.subgoal_info[channel]["subs"][now.month - 1]
        incentive = self.subgoal_info[channel]["incentive"]
        month = now.strftime("%B")

        if goal == 0:
            return "There currently isn't a subgoal for this month, but subs are all still massively appreciated for those that are able to!"

        if current < goal:
            return f"We are currently at {current} / {goal} subs for {month}. If the goal is hit, we will be doing {incentive} next month!"
        else:
            return f"Our subgoal for {month} was hit! We'll be doing {incentive} next month."

    @commands.command()
    async def subgoal(self, ctx: commands.Context):
        streamer = await ctx.message.channel.user()
        msg = await self.get_subgoal_msg(ctx.message.channel.name)
        await self.post_chat_announcement(streamer, msg)

    @commands.command()
    async def setsubgoal(self, ctx: commands.Context):
        if ctx.message.author.is_broadcaster:
            params = ctx.message.content[len("!setsubgoal"):].strip().split(" ", 1)
            if len(params) != 2:
                await ctx.send(f"{ctx.message.author.mention} !setsubgoal needs an integer goal and a message to be displayed. A goal of 0 will not show a sub goal in the !subgoal command")
                return
            channel = ctx.message.channel.name.lower()
            self.subgoal_info[channel]["goal"] = int(params[0])
            self.subgoal_info[channel]["incentive"] = params[1]
            await ctx.send(f"{ctx.message.author.mention} subgoal set to {self.subgoal_info[channel]['goal']} with the goal \"{self.subgoal_info[channel]['incentive']}\"")
            self.save_subgoal_data()

    #####################################################################################################
    # pubsub
    #####################################################################################################
    async def setup_pubsub(self, channel: str):
        self.pubsub[channel] = pubsub.PubSubPool(self)
        topics = [
            pubsub.bits(os.environ.get(f"TWITCH_CHANNEL_TOKEN_{channel}"))[int(os.environ.get(f"TWITCH_CHANNEL_ID_{channel}"))],
            pubsub.channel_points(os.environ.get(f"TWITCH_CHANNEL_TOKEN_{channel}"))[int(os.environ.get(f"TWITCH_CHANNEL_ID_{channel}"))],
            pubsub.channel_subscriptions(os.environ.get(f"TWITCH_CHANNEL_TOKEN_{channel}"))[int(os.environ.get(f"TWITCH_CHANNEL_ID_{channel}"))]
        ]
        await self.pubsub[channel].subscribe_topics(topics)

    async def event_pubsub_bits(self, event: pubsub.PubSubBitsMessage):
        print(f"Bits [{event.bits_used}] from {event.user.name}")

    async def event_pubsub_channel_points(self, event: pubsub.PubSubChannelPointsMessage):
        print(f"Channel Point Redemption [{event.timestamp}]: {event.user.name} - {event.reward.title} - {event.input}")

    async def event_pubsub_channel_subscriptions(self, event: pubsub.PubSubChannelSubscribe):
        sub_type = f"{event.sub_plan_name} Gift from \"{event.user.name if event.user else 'anonymous'}\"" if event.is_gift else event.sub_plan_name
        subscriber = event.recipient if event.is_gift else event.user
        print(f"Sub [{sub_type}]: {subscriber.name} subscribed for {event.cumulative_months}")
        self.subgoal_info[event.channel.name.lower()]["subs"][event.time.month - 1] += 1
        self.save_subgoal_data()

def run_twitch_bot(sharedResources) -> PhantomGamesBot:
    bot = PhantomGamesBot(sharedResources)
    bot.loop.create_task(bot.setup_pubsub("phantom5800"))
    return bot
