import asyncio
from copy import deepcopy
from datetime import datetime
import json
import os
import discord
import random
from discord.ext import bridge, commands
from commands.anilist import Anilist
from commands.custom_commands import CustomCommands
from commands.markov import MarkovHandler
from commands.quotes import QuoteHandler
from commands.slots import Slots
from commands.slots import SlotsMode
from commands.src import SrcomApi
from utils.utils import *

class PhantomGamesBot(bridge.Bot):
    def __init__(self, customCommandHandler: CustomCommands):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=os.environ['BOT_PREFIX'],
            intents=intents
        )

        self.custom = customCommandHandler

        # status messages
        self.messages = [
            "Responding to !speed",
            "!boris",
            "Paper Mario Randomizer",
            "WABITR"
        ]
        self.commands_since_new_status = 0

        # define reaction roles
        self.role_message_id = int(os.environ['DISCORD_ROLE_MESSAGE_ID']) # message to look for reactions on
        with open('./frontend/data/discord_emoji_roles.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.emoji_to_role = deepcopy(data)
                print(f"Emoji -> Role Mapping: {self.emoji_to_role}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load emoji->role mapping JSON")

    async def set_random_status(self):
        status = self.messages[random.randrange(len(self.messages))]
        print(f"[Status] {status}")
        message = discord.Game(status)
        await self.change_presence(activity=message)

    async def on_ready(self):
        print("=======================================")
        print(f"Discord [{datetime.now()}]: {self.user} is online!")
        print("=======================================")
        await self.set_random_status()

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

        old_status_count = self.commands_since_new_status
        # in discord, @'d users or roles are replaced with an id like: <@!895540229702828083>
        if message is not None:
            if message.content is not None and len(message.content) > 0:
                command = message.content.split()[0]
                response = self.custom.parse_custom_command(command, "phantom5800")
                if response is not None:
                    self.commands_since_new_status += 1

                    response = response.replace("/announce", "") # remove twitch specific slash commands
                    response = await replace_vars_generic(response)
                    await ctx.send(response)
                else:
                    await super().on_message(message)
            else:
                await super().on_message(message)
        
        # get new status sometimes
        if old_status_count != self.commands_since_new_status:
            if self.commands_since_new_status >= 100 or random.randrange(self.commands_since_new_status, 100) > 75:
                await self.set_random_status()

'''
Unlike twitchio, discord bot is unable to embed commands directly, and requires cogs.
'''
class PhantomGamesBotModule(commands.Cog):
    def __init__(self, bot: PhantomGamesBot, quoteHandler: QuoteHandler, srcHandler: SrcomApi, markovHandler: MarkovHandler):
        self.bot = bot
        self.quotes = quoteHandler
        self.speedrun = srcHandler
        self.markov = markovHandler
        self.anilist = Anilist()
        self.slots = Slots(SlotsMode.DISCORD)
    
    @bridge.bridge_command(brief="Get a link to the bot's github.", help="Get a link to the bot's github.")
    async def bot(self, ctx: commands.Context):
        await ctx.respond("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @bridge.bridge_command(name="commands", 
        brief="Get a list custom commands created on twitch.",
        help="Get a list of all basic response commands. These commands are all added by moderators on twitch.")
    async def get_commands(self, ctx):
        command_list = []
        command_list.extend(self.bot.custom.get_command_list())
        command_list.sort()
        await ctx.respond(f"List of all the current custom commands: {command_list}")

    @bridge.bridge_command(name="pb", 
        brief="Get a list of personal bests for a specified game.", 
        usage="game_name",
        help="Get a list of all PB's for a given game.\nUsage:\n\t!pb {Game name}\n\tExample: !pb paper mario")
    async def get_pb(self, ctx):
        game = ctx.message.content[3:].strip()
        self.bot.commands_since_new_status += 1
        if len(game) > 0:
            categories = self.speedrun.get_categories(game)
            response = ""
            for category in categories:
                response += self.speedrun.get_pb(game, category, True) + "\n"
            await ctx.respond(response)
        else:
            game_list = self.speedrun.get_games()
            await ctx.respond(f"Available games: {game_list}")

    @bridge.bridge_command(name="speed",
        brief="Recommends the caller a random game from speedrun.com")
    async def get_random_game(self, ctx):
        name = ctx.message.content[len("!speed"):].strip()
        game = None
        self.bot.commands_since_new_status += 1
        if name is not None and len(name) > 0:
            if name.startswith("user:"):
                message = await ctx.respond("One second, looking up users on src can take a bit")
                name = name[len("user:"):]
                game = self.speedrun.get_random_user_game(name)
                await message.respond(content=f"Would be really cool if {name} would speedrun {game}!")
                return
            else:
                game = self.speedrun.get_random_category(name)
        else:
            game = self.speedrun.get_random_game()
        await ctx.respond(f"{ctx.message.author.mention} You should try speedrunning {game}!")

    @bridge.bridge_command(name="anime",
        brief="Recommends the caller a random anime from anilist")
    async def get_random_anime(self, ctx):
        anime = self.anilist.getRandomAnimeName()
        self.bot.commands_since_new_status += 1
        await ctx.respond(f"{ctx.message.author.mention} You should try watching \"{anime}\"!")

    @bridge.bridge_command(name="animeinfo",
        brief="Gets a synopsis of a given anime",
        usage="<anime name>")
    async def get_anime_info(self, ctx):
        name =  ctx.message.content[len("!animeinfo"):].strip()
        anime_info = self.anilist.getAnimeByName(name)
        self.bot.commands_since_new_status += 1
        if anime_info is not None:
            embed = discord.Embed(color=0xA0DB8E)
            embed = self.anilist.formatDiscordAnimeEmbed(name, embed)
            await ctx.respond(f"{ctx.message.author.mention}", embed=embed)
        else:
            await ctx.respond(f"Could not find anime {name}")

    @bridge.bridge_command(name="quote", 
        brief="Get a random or specific quote.",
        usage="[quote id]",
        help="Get a quote that has been added on twitch.\nUsage:\n\t!quote - Get a random quote\n\t!quote {#} - Get a specific quote by id\n\tExample: !quote 3")
    async def get_quote(self, ctx, quote_id: str = "-1"):
        response = None

        if "latest" in quote_id.lower():
            await ctx.respond(self.quotes.pick_specific_quote(str(self.quotes.num_quotes() - 1)))
            return

        quote = tryParseInt(quote_id, -1)
        self.bot.commands_since_new_status += 1
        if quote >= 0:
            response = self.quotes.pick_specific_quote(quote_id)
        elif quote_id == "-1":
            response = self.quotes.pick_random_quote()
        else:
            response = self.quotes.find_quote_keyword(quote_id)
        if response is not None:
            await ctx.respond(response)

    @bridge.bridge_command(name="slots")
    async def get_slots(self, ctx):
        await ctx.respond(self.slots.roll(""))

    @bridge.bridge_command(name="chat")
    async def gen_chat_msg(self, ctx):
        response = self.markov.get_markov_string()
        self.bot.commands_since_new_status += 1
        await ctx.respond(response)
        try:
            await ctx.message.delete()
        except:
            return

    @bridge.bridge_command(name="ftoc")
    async def farenheit_to_celcius(self, ctx, farenheit: int):
        await ctx.respond(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @bridge.bridge_command(name="ctof")
    async def celcius_to_farenheit(self, ctx, celcius: int):
        await ctx.respond(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")

def run_discord_bot(eventLoop, customCommandHandler: CustomCommands, quoteHandler: QuoteHandler, srcHandler: SrcomApi, markovHandler: MarkovHandler):
    bot = PhantomGamesBot(customCommandHandler)
    bot.add_cog(PhantomGamesBotModule(bot, quoteHandler, srcHandler, markovHandler))
    async def runBot():
        await bot.start(os.environ['DISCORD_TOKEN'])

    eventLoop.create_task(runBot())
