from datetime import datetime
import os
import re
from twitchio.ext import commands
from twitchio.ext import routines
import commands.custom_commands as custom
import commands.quotes as quotes
import commands.src as src
from utils.utils import *

class PhantomGamesBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
            initial_channels=[os.environ['CHANNEL']]
        )

        # command handlers
        self.custom = custom.CustomCommands()
        self.quotes = quotes.QuoteHandler()
        self.speedrun = src.SrcomApi()

        # custom timers
        self.timer_queue = []
        self.current_timer_msg = 0
        self.messages_since_timer = 0
        self.timer_lines = tryParseInt(os.environ['TIMER_CHAT_LINES'], 5)
    
    async def load_timer_events(self):
        with open('./commands/resources/timer_events.txt', 'r', encoding="utf-8") as txt_file:
            lines = txt_file.readlines()
            for line in lines:
                command = line.strip()
                if self.custom.command_exists(command) and command not in self.timer_queue:
                    self.timer_queue.append(command)
        print(f"Timer events loaded: {self.timer_queue}")

    async def save_timer_events(self):
        with open('./commands/resources/timer_events.txt', 'w', encoding="utf-8") as txt_file:
            for event in self.timer_queue:
                txt_file.write(f"{event}\n")

    '''
    Called when the bot is ready to accept messages.
    '''
    async def event_ready(self):
        # load relevant data
        print("=======================================")
        await self.custom.load_commands()
        print("=======================================")
        await self.quotes.load_quotes()
        print("=======================================")
        await self.load_timer_events()
        print("=======================================")
        print(f"{os.environ['BOT_NICK']} is online!")
        print("=======================================")

        # start message timer
        self.timer_update.start(self.get_channel(os.environ['CHANNEL']))

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
    Runs every time a message is sent in chat.
    '''
    async def event_message(self, message):
        # make sure the bot ignores itself and the streamer
        if (message.author is not None and message.author.name.lower() == os.environ['BOT_NICK'].lower()) or message.author is None:
            return

        # get the context of the current message
        ctx = await self.get_context(message)

        # track chat messages that have been posted since the last timer fired
        self.messages_since_timer += 1

        if message.content is not None: # this has come up before??
            # handle custom commands
            if message.content is not None and len(message.content) > 0:
                command = message.content.split()[0]
                response = await self.custom.parse_custom_command(command)
                if response is not None:
                    await ctx.send(replace_vars(response, ctx))
                else:
                    await super().event_message(message)

    '''
    Periodic routine to send timer based messages.
    '''
    @routines.routine(minutes=int(os.environ['TIMER_MINUTES']), wait_first=True)
    async def timer_update(self, channel):
        if self.messages_since_timer >= self.timer_lines and len(self.timer_queue) > 0:
            self.messages_since_timer = 0

            message = self.custom.get_command(self.timer_queue[self.current_timer_msg])
            if message is None:
                print(f"[ERROR] {self.timer_queue[self.current_timer_msg]} is not a valid command for timers.")
            else:
                await channel.send(message)
                self.current_timer_msg = (self.current_timer_msg + 1) % len(self.timer_queue)
    
    # custom commands
    '''
    Utility function for command parsing to break up segments of commands.
    '''
    def command_msg_breakout(self, message: str) -> str:
        # TODO: theoretical regex match for command parsing
        # regex that might work: (?:[!]\w+) |(?:.*)
        # "!addcommand !newcommand command response" should give four matches
        #    !addcommand
        #    !newcommand
        #    command response
        #    {empty match in index 3}
        # "!addcommand newcommand command response" should give three matches, 
        # either need a better regex, or do extra work for this case
        #    !addcommand
        #    newcommand command response
        #    {empty match in index 2}

        msg_parts = message.split(' ', 3)
        if len(msg_parts) > 2:
            command_prefix_len = len(msg_parts[0]) + len(msg_parts[1]) + 2
            msg_parts[2] = message[command_prefix_len:]
        return msg_parts

    '''
    Add a custom command through twitch chat.
    '''
    @commands.command(aliases=["addcom"])
    async def addcommand(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                # find the intended command name
                command = command_parts[1]
                if len(command_parts) > 2:
                    # get the command response
                    command_response = command_parts[2]
                    # attempt to add the command
                    command_added = await self.custom.add_command(command, command_response, 0)
                    if command_added:
                        await ctx.send(f"{ctx.message.author.mention} Successfully added command [{command}] -> {command_response}")
                    else:
                        await ctx.send(f"{ctx.message.author.mention} Command [{command}] already exists.")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] needs a response message!")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")
    
    '''
    Set cooldown on a custom command through twitch chat.
    '''
    @commands.command()
    async def setcooldown(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                command = command_parts[1]
                if len(command_parts) > 2:
                    cooldown = tryParseInt(command_parts[2])
                    command_edited = await self.custom.set_cooldown(command, cooldown)
                    if command_edited:
                        await ctx.send(f"{ctx.message.author.mention} Cooldown for [{command}] = {cooldown} seconds.")
                    else:
                        await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] needs a cooldown specified in seconds.")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a cooldown!")

    '''
    Edit a custom command through twitch chat.
    '''
    @commands.command(aliases=["editcom"])
    async def editcommand(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                command = command_parts[1]
                if len(command_parts) > 2:
                    command_response = command_parts[2]
                    command_edited = await self.custom.edit_command(command, command_response, 0)
                    if command_edited:
                        await ctx.send(f"{ctx.message.author.mention} Edited command [{command}] -> {command_response}")
                    else:
                        await ctx.send(f"{ctx.message.author.mention} Command [{command}] does not exist.")
                else:
                    await ctx.send(f"{ctx.message.author.mention} Command [{command}] needs a response message!")
            else:
                await ctx.send(f"{ctx.message.author.mention} make sure to specify a command and a response!")

    '''
    Delete a custom command through twitch chat.
    '''
    @commands.command(aliases=["removecom"])
    async def removecommand(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                command = command_parts[1]
                command_removed = await self.custom.remove_command(command)
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
                self.timer_update.start(self.get_channel(os.environ['CHANNEL']))
            except RuntimeError:
                await ctx.send(f"{ctx.message.author.mention} Timers are already enabled")
                return
            await ctx.send(f"{ctx.message.author.mention} Timers have been enabled")

    @commands.command()
    async def addtimer(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                command = command_parts[1]
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
    async def removetimer(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1:
                command = command_parts[1]
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
    async def quote(self, ctx: commands.Context):
        quote_id = ctx.message.content.split(' ', 2)
        response = None
        if len(quote_id) > 1 and tryParseInt(quote_id[1], -1) >= 0:
            response = await self.quotes.pick_specific_quote(quote_id[1])
        else:
            response = await self.quotes.pick_random_quote()
        if response is not None:
            await ctx.send(response)

    @commands.command()
    async def addquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            new_quote = ctx.message.content[ctx.message.content.index(' ') + 1:]
            game_name = await get_game_name_from_twitch(self)
            response = await self.quotes.add_quote(new_quote, game_name)
            await ctx.send(response)

    @commands.command()
    async def editquote(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 2 and tryParseInt(command_parts[1], -1) >= 0:
                quote_id = int(command_parts[1])
                quote = command_parts[2]
                response = await self.quotes.edit_quote(quote_id, quote)
                await ctx.send(response)
    
    @commands.command()
    async def removequote(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            command_parts = self.command_msg_breakout(ctx.message.content)
            if len(command_parts) > 1 and tryParseInt(command_parts[1], -1) >= 0:
                quote_id = int(command_parts[1])
                response = await self.quotes.remove_quote(quote_id)
                await ctx.send(response)

    # speedrun.com
    '''
    Get the personal best time for a game/category on speedrun.com.
    '''
    @commands.command()
    async def pb(self, ctx: commands.Context):
        if len(os.environ['SRC_USER']) > 0:
            category = ctx.message.content[4:] # TODO: cut out unicode whitespace that 7tv sometimes appends
            game = await get_game_name_from_twitch(self)
            response = self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
            await ctx.send(replace_vars(response, ctx))

    # stream commands
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
        game_name = await get_game_name_from_twitch(self)
        await ctx.send(game_name)

    '''
    Give a shoutout to a specific user in chat.
    '''
    @commands.command(aliases=["shoutout"])
    async def so(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            user = ctx.message.content.replace("!so", "").strip()
            game = await get_game_name_from_twitch_for_user(self, user)
            await ctx.send(f"Checkout {user}, maybe drop them a follow! They were most recently playing {game} over at https://twitch.tv/{user}")

    # social commands
    '''
    Get a link to the streamer's github profile if it exists.
    '''
    @commands.command()
    async def github(self, ctx: commands.Context):
        if len(os.environ['GITHUB']) > 0:
            await ctx.send(f"All my open source code projects are available on github: {os.environ['GITHUB']}")

    '''
    Get a link to the streamer's twitter profile if it exists.
    '''
    @commands.command()
    async def twitter(self, ctx: commands.Context):
        if len(os.environ['TWITTER']) > 0:
            await ctx.send(f"Follow me on twitter to keep up with current events: {os.environ['TWITTER']}")

    '''
    Get a link to the streamer's youtube channel if it exists.
    '''
    @commands.command()
    async def youtube(self, ctx: commands.Context):
        if len(os.environ['YOUTUBE']) > 0:
            await ctx.send(f"Follow my youtube for occasional speedrun related videos: {os.environ['YOUTUBE']}")

if __name__ == "__main__":
    bot = PhantomGamesBot()
    bot.run()
