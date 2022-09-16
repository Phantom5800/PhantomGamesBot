from datetime import datetime
import os
import random
import re
from typing import Optional
from twitchio import PartialUser
from twitchio.ext import commands
from twitchio.ext import routines
from commands.anilist import Anilist
from commands.custom_commands import CustomCommands
from commands.markov import MarkovHandler
from commands.quotes import QuoteHandler
from commands.slots import Slots
from commands.slots import SlotsMode
from commands.src import SrcomApi
from utils.utils import *

class PhantomGamesBot(commands.Bot):
    def __init__(self, customCommandHandler: CustomCommands, quoteHandler: QuoteHandler, srcHandler: SrcomApi, markovHandler: MarkovHandler):
        super().__init__(
            token=os.environ['TWITCH_OAUTH_TOKEN'],
            client_id=os.environ['TWITCH_CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
            initial_channels=[os.environ['TWITCH_CHANNEL']]
        )

        # command handlers
        self.custom = customCommandHandler
        self.quotes = quoteHandler
        self.speedrun = srcHandler
        self.markov = markovHandler
        self.anilist = Anilist()
        self.slots = Slots(SlotsMode.TWITCH)

        # custom timers
        self.timer_queue = []
        self.current_timer_msg = 0
        self.messages_since_timer = 0
        self.timer_lines = tryParseInt(os.environ['TIMER_CHAT_LINES'], 5)
        self.auto_chat_msg = 0
        self.auto_chat_lines_mod = tryParseInt(os.environ['AUTO_CHAT_LINES_MOD'], 10)
        self.auto_chat_lines = tryParseInt(os.environ['AUTO_CHAT_LINES_MIN'], 20) + random.randint(0, self.auto_chat_lines_mod)

        # markov
        self.markov_data_store = True
        self.markov_store_minlen = 6

        # links
        self.permitted_users = []
        self.link_protection = False
        self.url_search = re.compile(r"([\w+]+\:\/\/)?([\w\d-]+\.)*[\w-]+[\.]\w+([\/\?\=\&\#.]?[\w-]+)*\/?")

        # random message response
        self.bless_count = 0
        self.bless_sent = False

        # load relevant data
        self.load_timer_events()
        self.load_permitted_users()
        print("=======================================")
        print(f"Twitch: {os.environ['BOT_NICK']} is online!")
        print("=======================================")

        # start message timer
        try:
            self.timer_update.start()
            self.automatic_chat.start()
        except RuntimeError:
            print("Timer is already running")
    
    def load_timer_events(self):
        with open('./commands/resources/timer_events.txt', 'r', encoding="utf-8") as txt_file:
            lines = txt_file.readlines()
            for line in lines:
                command = line.strip()
                if self.custom.command_exists(command) and command not in self.timer_queue:
                    self.timer_queue.append(command)
        print(f"Timer events loaded: {self.timer_queue}")

    def save_timer_events(self):
        with open('./commands/resources/timer_events.txt', 'w', encoding="utf-8") as txt_file:
            for event in self.timer_queue:
                txt_file.write(f"{event}\n")

    def load_permitted_users(self):
        with open('./commands/resources/permitted_users.txt', 'r', encoding="utf-8") as txt_file:
            lines = txt_file.readlines()
            for line in lines:
                user = line.strip()
                if user not in self.permitted_users:
                    self.permitted_users.append(user)
    
    def save_permitted_users(self):
        with open('./commands/resources/permitted_users.txt', 'w', encoding="utf-8") as txt_file:
            for user in self.permitted_users:
                txt_file.write(f"{user}\n")

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
    Check to see if a user is able to post links in twitch chat.

    Allowed types of users should be mod, vip and subscribers.
    '''
    def user_can_post_links(self, user) -> bool:
        if user.name.lower() in self.permitted_users:
            return True
        return user.is_mod or user.is_subscriber or 'vip' in user.badges

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
        self.messages_since_timer += 1
        self.auto_chat_msg += 1

        if message is not None: # this has come up before??
            # handle custom commands
            if message.content is not None and len(message.content) > 0:
                # look for urls and delete messages if they are not mod/vip
                if self.link_protection and not self.user_can_post_links(message.author):
                    url_matches = self.url_search.search(message.content)
                    if url_matches is not None:
                        message_id = message.tags['id']
                        print(f"[Detected unpermitted link]: \"{message.content}\"\n\tfrom {message.author}\n\t{url_matches}")
                        await message.channel.send(f"/delete {message_id}")
                
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
                response = self.custom.parse_custom_command(command)
                if response is not None:
                    response = await replace_vars_twitch(response, ctx, self.get_channel(os.environ['TWITCH_CHANNEL']))
                    await ctx.send(response)
                else:
                    await super().event_message(message)

                    # save twitch messages that are not commands, links and meet a minimum length requirement
                    contains_link = "https://" in message.content
                    not_self_post = not message.content.startswith(os.environ['BOT_PREFIX'])
                    length_req = len(set(message.content.split())) >= self.markov_store_minlen
                    if self.markov_data_store and not contains_link and not_self_post and length_req:
                        with open("./commands/resources/markov/markov-2022.txt", "a+") as f:
                            try:
                                f.write(f"{message.content}\n")
                            except:
                                print(f"[ERROR] Failed to add string to markov: {message.content}")

    '''
    Periodic routine to send timer based messages.
    '''
    @routines.routine(minutes=int(os.environ['TIMER_MINUTES']), wait_first=True)
    async def timer_update(self):
        if self.messages_since_timer >= self.timer_lines and len(self.timer_queue) > 0:
            self.messages_since_timer = 0

            message = self.custom.get_command(self.timer_queue[self.current_timer_msg])
            if message is None:
                print(f"[ERROR] {self.timer_queue[self.current_timer_msg]} is not a valid command for timers.")
            else:
                channel = self.get_channel(os.environ['TWITCH_CHANNEL'])
                if channel is None:
                    print(f"[ERROR] Timer cannot find channel '{os.environ['TWITCH_CHANNEL']}' to post in??")
                else:
                    #await channel.send(f"/announce {message}")
                    await channel.send(message)
                    self.current_timer_msg = (self.current_timer_msg + 1) % len(self.timer_queue)
    
    '''
    Periodically posts automatically generated messages to chat.
    '''
    @routines.routine(minutes=int(os.environ['AUTO_CHAT_MINUTES']), wait_first=True)
    async def automatic_chat(self):
        if self.auto_chat_msg >= self.auto_chat_lines:
            self.auto_chat_msg = 0
            self.auto_chat_lines = tryParseInt(os.environ['AUTO_CHAT_LINES_MIN'], 20) + random.randint(0, self.auto_chat_lines_mod)

            channel = self.get_channel(os.environ['TWITCH_CHANNEL'])
            if channel is None:
                print(f"[ERROR] Timer cannot find channel '{os.environ['TWITCH_CHANNEL']}' to post in??")
            else:
                message = self.markov.get_markov_string()
                print(f"Generated Message: {message}")
                await channel.send(message)
    
    # custom commands
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
            pattern = r"([!]\w+) ([!]?\w+) (.*)"
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
            if "command" in key or ("quote" in key and key != "quote") or "timer" in key or "set" in key or key == "so":
                continue
            command_list.append(f"!{key}")
        command_list.extend(self.custom.get_command_list())
        command_list.sort()
        await ctx.send(f"List of all the current commands: {command_list}")

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
                command_added = self.custom.add_command(command, command_response, 0)
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
                command_edited = self.custom.set_cooldown(command, cooldown)
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
                command_edited = self.custom.edit_command(command, command_response, 0)
                if command_edited:
                    await ctx.send(f"{ctx.message.author.mention} Edited command [{command}] -> {command_response}")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")

    '''
    Delete a custom command through twitch chat.
    '''
    @commands.command(aliases=["removecom"])
    async def removecommand(self, ctx: commands.Context, command: str = ""):
        if ctx.message.author.is_mod:
            if len(command) > 0:
                command_removed = self.custom.remove_command(command)
                if command_removed:
                    await ctx.send(f"{ctx.message.author.mention} Removed command [{command}]")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command!")

    # timer
    @commands.command()
    async def disabletimer(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            self.timer_update.cancel()
            await ctx.send(f"{ctx.message.author.mention} Timers have been disabled")

    @commands.command()
    async def enabletimer(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            try:
                self.timer_update.start()
            except RuntimeError:
                await ctx.send(f"{ctx.message.author.mention} Timers are already enabled")
                return
            await ctx.send(f"{ctx.message.author.mention} Timers have been enabled")

    @commands.command()
    async def addtimer(self, ctx: commands.Context, command: str = ""):
        if ctx.message.author.is_mod:
            if len(command) > 0:
                if self.custom.command_exists(command):
                    if command not in self.timer_queue:
                        self.timer_queue.append(command)
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
            if len(command) > 0:
                if command in self.timer_queue:
                    self.timer_queue.remove(command)
                    await self.save_timer_events()
                    await ctx.send(f"{ctx.message.author.mention} [{command}] has been removed from the timer")
            else:
                await ctx.send(f"{ctx.message.author.mention} Specify a command to remove from the timer")
    
    @commands.command()
    async def timerevents(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            await ctx.send(f"Current timer events: {self.timer_queue}")

    # quotes
    @commands.command()
    async def chat(self, ctx: commands.Context):
        response = self.markov.get_markov_string()
        await ctx.send(response)

    @commands.command()
    async def quote(self, ctx: commands.Context, quote_id: str = "-1"):
        response = None

        if "latest" in quote_id.lower():
            await ctx.send(self.quotes.pick_specific_quote(str(self.quotes.num_quotes() - 1)))
            return

        quote = tryParseInt(quote_id, -1)
        if quote >= 0:
            response = self.quotes.pick_specific_quote(quote_id)
        elif quote_id == "-1":
            response = self.quotes.pick_random_quote()
        else:
            response = self.quotes.find_quote_keyword(quote_id)
        if response is not None:
            await ctx.send(response)

    @commands.command()
    async def addquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod or 'vip' in ctx.message.author.badges:
            command_parts = self.command_msg_breakout(ctx.message.content, 2)
            if command_parts is not None and len(command_parts) > 1:
                new_quote = command_parts[1]
                if len(new_quote) > 0:
                    game_name = await get_game_name_from_twitch(self)
                    response = self.quotes.add_quote(new_quote, game_name)
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
                response = self.quotes.edit_quote(quote_id, quote)
                await ctx.send(response)
    
    @commands.command()
    async def removequote(self, ctx: commands.Context, quote_id: str = "-1"):
        if ctx.message.author.is_mod:
            if tryParseInt(quote_id, -1) >= 0:
                response = self.quotes.remove_quote(int(quote_id))
                await ctx.send(response)

    # allowing links in chat
    @commands.command()
    async def permit(self, ctx: commands.Context, user: PartialUser = None):
        if ctx.message.author.is_mod:
            if user is not None:
                lowername = user.name.lower()
                if lowername not in self.permitted_users:
                    self.permitted_users.append(lowername)
                    self.save_permitted_users()
                    await ctx.send(f"{user.name} can now post links")

    @commands.command()
    async def unpermit(self, ctx: commands.Context, user: PartialUser = None):
        if ctx.message.author.is_mod:
            if user is not None:
                lowername = user.name.lower()
                if lowername in self.permitted_users:
                    self.permitted_users.remove(lowername)
                    self.save_permitted_users()
                    await ctx.send(f"{user.name} is no longer allowed to post links")

    @commands.command()
    async def enablelinks(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            self.link_protection = False
            await ctx.send("Link protection has been disabled")

    @commands.command()
    async def disablelinks(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            self.link_protection = True
            await ctx.send("Link protection has been enabled")

    # speedrun.com
    '''
    Get the personal best time for a game/category on speedrun.com. This command does take a few seconds to respond while it performs a search.
    '''
    @commands.command()
    async def pb(self, ctx: commands.Context):
        if len(os.environ['SRC_USER']) > 0:
            category = ctx.message.content[3:].strip()
            game = await get_game_name_from_twitch(self)
            response = self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
            await ctx.send(response)

    @commands.command()
    async def speed(self, ctx):
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

    # anilist
    @commands.command()
    async def anime(self, ctx):
        anime = self.anilist.getRandomAnimeName()
        await ctx.send(f"{ctx.message.author.mention} You should try watching \"{anime}\"!")

    # stream commands
    '''
    Get information about the bot itself.
    '''
    @commands.command()
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    '''
    Attempt to get how long a user has been following the channel for.
    '''
    @commands.command()
    async def followage(self, ctx: commands.Context):
        streamer = await get_twitch_user(self, os.environ['TWITCH_CHANNEL'])
        try:
            followEvent = await ctx.message.author.fetch_follow(to_user=streamer, token=os.environ['TWITCH_OAUTH_TOKEN'])
            print(followEvent)
        except Exception as e:
            print(e)
            await ctx.send(f"{ctx.message.author.mention} something went wrong, oops")
            return
        if followEvent is not None:
            await ctx.send(f"{ctx.message.author.mention} has been following for {followEvent.followed_at}!")
        else:
            await ctx.send(f"{ctx.message.author.mention} is not even following phanto274Shrug")

    '''
    Get the current game being played on twitch.
    '''
    @commands.command()
    async def game(self, ctx: commands.Context):
        game_name = await get_game_name_from_twitch(self)
        await ctx.send(game_name)

    @commands.command()
    @commands.cooldown(1, 10, commands.Bucket.user)
    async def slots(self, ctx: commands.Context):
        await ctx.send(self.slots.roll(ctx.message.author.mention))

    '''
    Give a shoutout to a specific user in chat.
    '''
    @commands.command(aliases=["shoutout"])
    async def so(self, ctx: commands.Context, user: PartialUser = None):
        if ctx.message.author.is_mod and user is not None:
            game = await get_game_name_from_twitch_for_user(self, user.name)
            await ctx.send(f"Checkout {user.name}, maybe drop them a follow! They were most recently playing {game} over at https://twitch.tv/{user.name}")
        
    '''
    Get the current title of the stream.
    '''
    @commands.command()
    async def title(self, ctx: commands.Context):
        streamtitle = await get_stream_title_for_user(self, os.environ['TWITCH_CHANNEL'])
        await ctx.send(streamtitle)

def run_twitch_bot(customCommandHandler: CustomCommands, quoteHandler: QuoteHandler, srcHandler: SrcomApi, markovHandler: MarkovHandler) -> PhantomGamesBot:
    bot = PhantomGamesBot(customCommandHandler, quoteHandler, srcHandler, markovHandler)
    return bot
