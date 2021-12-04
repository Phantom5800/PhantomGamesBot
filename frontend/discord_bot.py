import asyncio
import discord
from discord.ext import commands
import os
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from utils.utils import *

class PhantomGamesBot(commands.Bot):
    def __init__(self, customCommandHandler: CustomCommands):
        super().__init__(
            command_prefix=os.environ['BOT_PREFIX']
        )

        self.custom = customCommandHandler

    async def on_ready(self):
        print("=======================================")
        print(f"Discord: {self.user} is online!")
        print("=======================================")

    '''
    Handle custom commands.
    '''
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        # get the message context so that we don't have to reply
        ctx = await self.get_context(message)

        if message is not None:
            if message.content is not None and len(message.content) > 0:
                command = message.content.split()[0]
                response = self.custom.parse_custom_command(command)
                if response is not None:
                    await ctx.send(response)
                else:
                    await super().on_message(message)

'''
Unlike twitchio, discord bot is unable to embed commands directly, and requires cogs.
'''
class PhantomGamesBotModule(commands.Cog):
    def __init__(self, bot, quoteHandler: QuoteHandler):
        self.bot = bot
        self.quotes = quoteHandler
    
    @commands.command()
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @commands.command(name="quote")
    async def get_quote(self, ctx, quote_id: str = "-1"):
        response = None
        if tryParseInt(quote_id, -1) >= 0:
            response = self.quotes.pick_specific_quote(quote_id)
        else:
            response = self.quotes.pick_random_quote()
        if response is not None:
            await ctx.send(response)

def run_discord_bot(eventLoop, customCommandHandler: CustomCommands, quoteHandler: QuoteHandler):
    bot = PhantomGamesBot(customCommandHandler)
    bot.add_cog(PhantomGamesBotModule(bot, quoteHandler))
    eventLoop.create_task(bot.start(os.environ['DISCORD_TOKEN']))
