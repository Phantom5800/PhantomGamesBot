import datetime
import os
import re
import threading
import time
from twitchio.ext import commands
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
        self.messages_since_timer = 0
        self.timer_minutes = tryParseInt(os.environ['TIMER_MINUTES'], 10)
        self.last_timer_fire = datetime.now()
        self.timer_lines = tryParseInt(os.environ['TIMER_CHAT_LINES'], 5)
        self.timer_enabled = False
    
    '''
    Called when the bot is ready to accept messages.
    '''
    async def event_ready(self):
        # load relevant data
        print("=======================================")
        await self.custom.load_commands()
        await self.quotes.load_quotes()
        self.timer_thread.start()
        print(f"{os.environ['BOT_NICK']} is online!")
        print("=======================================")

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
        if self.timer_enabled:
            self.messages_since_timer += 1
            if self.messages_since_timer >= self.timer_lines:
                if (datetime.now() - self.last_timer_fire).total_seconds() / 60 > self.timer_minutes:
                    self.last_timer_fire = datetime.now()
                    self.messages_since_timer = 0
                    await ctx.send("HAHA")

        # respond to messages @'ing the bot with the same message
        if message.content.lower().startswith("@" + os.environ['BOT_NICK'].lower()):
            bot_name_len = len("@" + os.environ['BOT_NICK'])
            await ctx.send(message.author.mention + message.content.lower()[bot_name_len:])

        # handle meme based commands
        custom_msg_handled = await self.custom.parse_custom_command(message.content, ctx)
        if custom_msg_handled == False:
            await super().event_message(message)
    
    # custom commands
    def command_msg_breakout(self, message: str) -> str:
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
            self.timer_enabled = False
            await ctx.send("Timers have been disabled")

    @commands.command()
    async def enabletimer(self, ctx: commands.Context):
        if ctx.message.author.is_mod:
            self.timer_enabled = True
            await ctx.send("Timers have been enabled")

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
            response = await self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
            await ctx.send(response)

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
