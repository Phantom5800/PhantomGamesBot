import os
import re
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

        self.custom = custom.CustomCommands()
        self.quotes = quotes.QuoteHandler()
        self.speedrun = src.SrcomApi()
        self.messages_since_timer = 0
        self.timer_minutes = tryParseInt(os.environ['TIMER_MINUTES'], 10)
        self.timer_lines = tryParseInt(os.environ['TIMER_CHAT_LINES'], 5)
    
    async def event_ready(self):
        'Called when the bot is ready to accept messages.'
        # load relevant data
        print("=======================================")
        await self.custom.load_commands()
        await self.quotes.load_quotes()
        print(f"{os.environ['BOT_NICK']} is online!")
        print("=======================================")

    async def event_command_error(self, ctx: commands.Context, error: Exception):
        # ignore command errors that exist in the custom command set
        return
        # command is None??? idk, figure this out later
        # if self.custom.command_exists(ctx.command.name):
        #     return
        # super().event_command_error(ctx, error)

    async def event_message(self, message):
        'Runs every time a message is sent in chat.'

        # make sure the bot ignores itself and the streamer
        if (message.author is not None and message.author.name.lower() == os.environ['BOT_NICK'].lower()) or message.author is None:
            return

        # track chat messages that have been posted since the last timer fired
        self.messages_since_timer += 1

        # respond to messages @'ing the bot with the same message
        ctx = await self.get_context(message)
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
    @commands.command()
    async def pb(self, ctx: commands.Context):
        if len(os.environ['SRC_USER']) > 0:
            category = ctx.message.content[4:] # TODO: cut out unicode whitespace that 7tv sometimes appends
            game = await get_game_name_from_twitch(self)
            response = await self.speedrun.get_pb(convert_twitch_to_src_game(game), category)
            await ctx.send(response)

    # stream commands
    @commands.command()
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @commands.command()
    async def game(self, ctx: commands.Context):
        game_name = await get_game_name_from_twitch(self)
        await ctx.send(game_name)

    # social commands
    @commands.command()
    async def github(self, ctx: commands.Context):
        if len(os.environ['GITHUB']) > 0:
            await ctx.send(f"All my open source code projects are available on github: {os.environ['GITHUB']}")

    @commands.command()
    async def twitter(self, ctx: commands.Context):
        if len(os.environ['TWITTER']) > 0:
            await ctx.send(f"Follow me on twitter to keep up with current events: {os.environ['TWITTER']}")

    @commands.command()
    async def youtube(self, ctx: commands.Context):
        if len(os.environ['YOUTUBE']) > 0:
            await ctx.send(f"Follow my youtube for occasional speedrun related videos: {os.environ['YOUTUBE']}")

if __name__ == "__main__":
    bot = PhantomGamesBot()
    bot.run()
