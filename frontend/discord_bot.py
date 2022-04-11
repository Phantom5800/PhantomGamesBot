import asyncio
from copy import deepcopy
import json
import os
import discord
from discord.ext import commands
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from commands.src import SrcomApi
from commands.anilist import Anilist
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

        message = discord.Game("Responding to !speed")
        await self.change_presence(activity=message)

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
    def __init__(self, bot, quoteHandler: QuoteHandler, srcHandler: SrcomApi):
        self.bot = bot
        self.quotes = quoteHandler
        self.speedrun = srcHandler
        self.anilist = Anilist()
    
    @commands.command(brief="Get a link to the bot's github.", help="Get a link to the bot's github.")
    async def bot(self, ctx: commands.Context):
        await ctx.send("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @commands.command(name="commands", 
        brief="Get a list custom commands created on twitch.",
        help="Get a list of all basic response commands. These commands are all added by moderators on twitch.")
    async def get_commands(self, ctx):
        command_list = []
        command_list.extend(self.bot.custom.get_command_list())
        command_list.sort()
        await ctx.send(f"List of all the current custom commands: {command_list}")

    @commands.command(name="pb", 
        brief="Get a list of personal bests for a specified game.", 
        usage="game_name",
        help="Get a list of all PB's for a given game.\nUsage:\n\t!pb {Game name}\n\tExample: !pb paper mario")
    async def get_pb(self, ctx):
        game = ctx.message.content[3:].strip()
        if len(game) > 0:
            categories = self.speedrun.get_categories(game)
            response = ""
            for category in categories:
                response += self.speedrun.get_pb(game, category, True) + "\n"
            await ctx.send(response)
        else:
            game_list = self.speedrun.get_games()
            await ctx.send(f"Available games: {game_list}")

    @commands.command(name="speed",
        brief="Recommends the caller a random game from speedrun.com")
    async def get_random_game(self, ctx):
        name = ctx.message.content[len("!speed"):].strip()
        game = None
        if name is not None and len(name) > 0:
            if name.startswith("user:"):
                message = await ctx.send("One second, looking up users on src can take a bit")
                name = name[len("user:"):]
                game = self.speedrun.get_random_user_game(name)
                await message.edit(content=f"Would be really cool if {name} would speedrun {game}!")
                return
            else:
                game = self.speedrun.get_random_category(name)
        else:
            game = self.speedrun.get_random_game()
        await ctx.send(f"{ctx.message.author.mention} You should try speedrunning {game}!")

    @commands.command(name="anime",
        brief="Recommends the caller a random anime from anilist")
    async def get_random_anime(self, ctx):
        anime = self.anilist.getRandomAnimeName()
        await ctx.send(f"{ctx.message.author.mention} You should try watching \"{anime}\"!")

    @commands.command(name="animeinfo",
        brief="Gets a synopsis of a given anime",
        usage="<anime name>")
    async def get_anime_info(self, ctx):
        name =  ctx.message.content[len("!animeinfo"):].strip()
        anime_info = self.anilist.getAnimeByName(name)
        if anime_info is not None:
            embed = discord.Embed(color=0xA0DB8E)
            embed = self.anilist.formatDiscordAnimeEmbed(name, embed)
            await ctx.send(f"{ctx.message.author.mention}", embed=embed)
        else:
            await ctx.send(f"Could not find anime {name}")

    @commands.command(name="quote", 
        brief="Get a random or specific quote.",
        usage="[quote id]",
        help="Get a quote that has been added on twitch.\nUsage:\n\t!quote - Get a random quote\n\t!quote {#} - Get a specific quote by id\n\tExample: !quote 3")
    async def get_quote(self, ctx, quote_id: str = "-1"):
        response = None
        quote = tryParseInt(quote_id, -1)
        if quote >= 0:
            response = self.quotes.pick_specific_quote(quote_id)
        elif quote_id == "-1":
            response = self.quotes.pick_random_quote()
        else:
            response = self.quotes.find_quote_keyword(quote_id)
        if response is not None:
            await ctx.send(response)

def run_discord_bot(eventLoop, customCommandHandler: CustomCommands, quoteHandler: QuoteHandler, srcHandler: SrcomApi):
    bot = PhantomGamesBot(customCommandHandler)
    bot.add_cog(PhantomGamesBotModule(bot, quoteHandler, srcHandler))
    eventLoop.create_task(bot.start(os.environ['DISCORD_TOKEN']))
