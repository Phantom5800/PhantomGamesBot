import asyncio
from copy import deepcopy
import json
import os
import discord
from discord.ext import commands
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from utils.utils import *

class PhantomGamesBot(commands.Bot):
    def __init__(self, customCommandHandler: CustomCommands):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=os.environ['BOT_PREFIX'],
            intents=intents
        )

        self.custom = customCommandHandler

        # define reaction roles
        self.role_message_id = int(os.environ['DISCORD_ROLE_MESSAGE_ID']) # message to look for reactions on
        with open('./frontend/data/discord_emoji_roles.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.emoji_to_role = deepcopy(data)
                print(f"Emoji -> Role Mapping: {self.emoji_to_role}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load emoji->role mapping JSON")

    async def on_ready(self):
        print("=======================================")
        print(f"Discord: {self.user} is online!")
        print("=======================================")

    '''
    Add roles to users when selecting a reaction.
    '''
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        try:
            role_id = self.emoji_to_role[payload.emoji.name]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        try:
            await payload.member.add_roles(role)
        except discord.HTTPException:
            pass

    '''
    Remove roles from users that deselect a reaction.
    '''
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return
            
        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        try:
            role_id = self.emoji_to_role[payload.emoji.name]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            pass


    '''
    Handle custom commands.
    '''
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        # get the message context so that we don't have to reply
        ctx = await self.get_context(message)

        # in discord, @'d users or roles are replaced with an id like: <@!895540229702828083>
        if message is not None:
            if message.content is not None and len(message.content) > 0:
                command = message.content.split()[0]
                response = self.custom.parse_custom_command(command)
                if response is not None:
                    response = await replace_vars_generic(response)
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

    @commands.command(name="commands")
    async def get_commands(self, ctx):
        command_list = []
        command_list.extend(self.bot.custom.get_command_list())
        command_list.sort()
        await ctx.send(f"List of all the current custom commands: {command_list}")

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
