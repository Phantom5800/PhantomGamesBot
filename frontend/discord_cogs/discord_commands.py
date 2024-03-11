import discord
from commands.slots import Slots, SlotsMode
from discord.ext import bridge, commands
from utils.utils import *

# StrEnum was added in Python 3.11. For previous versions, you can install strenum with pip
try:
    from enum import StrEnum
except:
    from strenum import StrEnum

class SrcGames(StrEnum):
    PaperMario = "Paper Mario"
    MinishCap = "The Legend of Zelda: The Minish Cap"
    DogIsland = "THE DOG Island"

class YouTubePlaylists(StrEnum):
    BattleNetworkRando = "Battle Network Randomizers"
    LADXRando = "Link's Awakening Randomizers"
    MinishCapRando = "Minish Cap Randomizers"
    PaperMarioBlackPit = "Paper Mario Black Pit"
    PaperMarioRando = "Paper Mario Randomizers"
    PokemonCrystalRando = "Pokémon Crystal Randomizers"
    PokemonEmeraldRando = "Pokémon Emerald Randomizers"

'''
Unlike twitchio, discord bot is unable to embed commands directly, and requires cogs.
'''
class PhantomGamesBotCommands(commands.Cog):
    def __init__(self, bot, sharedResources):
        self.bot = bot
        self.quotes = sharedResources.quoteHandler
        self.speedrun = sharedResources.srcHandler
        self.markov = sharedResources.markovHandler
        self.anilist = sharedResources.anilist
        self.youtube = sharedResources.youtube
        self.slots = Slots(SlotsMode.DISCORD)
    
    @bridge.bridge_command(description="Get a link to the bot's github.", help="Get a link to the bot's github.")
    async def bot(self, ctx: commands.Context):
        await ctx.respond("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @bridge.bridge_command(name="commands", 
        description="Get a list custom commands created on twitch.",
        help="Get a list of all basic response commands. These commands are all added by moderators on twitch.")
    async def get_commands(self, ctx):
        command_list = []
        command_list.extend(self.bot.custom.get_command_list(self.account))
        command_list.sort()
        await ctx.respond(f"List of all the current custom commands: {command_list}")

    @bridge.bridge_command(name="pb", 
        description="Get a list of personal bests for a specified game.", 
        usage="game_name",
        help="Get a list of all PB's for a given game.\nUsage:\n\t!pb {Game name}\n\tExample: !pb paper mario")
    async def get_pb(self, ctx, game: SrcGames):
        self.bot.commands_since_new_status += 1
        await ctx.defer()
        categories = self.speedrun.get_categories(game)
        print(f"Categories found for {game}: {categories}")
        response = ""
        for category in categories:
            response += self.speedrun.get_pb(game, category, True) + "\n"
        await ctx.respond(response)

    @bridge.bridge_command(name="speed",
        description="Recommends the caller a random game from speedrun.com")
    @discord.option("search",
        description="Search term to use for speedrun.com. Prefix search with \"user:\" to do a username search instead.")
    async def get_random_game(self, ctx, search:str=""):
        name = search.strip()
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
        await ctx.respond(f"{ctx.author.mention} You should try speedrunning {game}!")

    @bridge.bridge_command(name="anime",
        description="Recommends the caller a random anime from anilist")
    async def get_random_anime(self, ctx):
        anime = self.anilist.getRandomAnimeName()
        self.bot.commands_since_new_status += 1
        await ctx.respond(f"{ctx.author.mention} You should try watching \"{anime}\"!")

    @bridge.bridge_command(name="animeinfo",
        description="Gets a synopsis of a given anime")
    @discord.option("anime",
        description="The anime to get info for.")
    async def get_anime_info(self, ctx, anime:str):
        name =  anime.strip()
        anime_info = self.anilist.getAnimeByName(name)
        self.bot.commands_since_new_status += 1
        if anime_info is not None:
            embed = discord.Embed(color=0xA0DB8E)
            embed = self.anilist.formatDiscordAnimeEmbed(name, embed)
            await ctx.respond(f"{ctx.author.mention}", embed=embed)
        else:
            await ctx.respond(f"Could not find anime {name}")

    @bridge.bridge_command(name="quote", 
        description="Get a random or specific quote.",
        help="Get a quote that has been added on twitch.\nUsage:\n\t!quote - Get a random quote\n\t!quote {#} - Get a specific quote by id\n\tExample: !quote 3")
    @discord.option("quote_id",
        description="The quote to lookup, can provide a word to search for among all quotes as well.")
    async def get_quote(self, ctx, quote_id: str = "-1"):
        response = None

        if "latest" in quote_id.lower():
            await ctx.respond(self.quotes.pick_specific_quote(str(self.quotes.num_quotes(self.bot.account) - 1), self.bot.account))
            return

        quote = tryParseInt(quote_id, -1)
        self.bot.commands_since_new_status += 1
        if quote >= 0:
            response = self.quotes.pick_specific_quote(quote_id, self.bot.account)
        elif quote_id == "-1":
            response = self.quotes.pick_random_quote(self.bot.account)
        else:
            response = self.quotes.find_quote_keyword(quote_id, self.bot.account)
        if response is not None:
            await ctx.respond(response)

    @bridge.bridge_command(name="slots",
        description="Roll the slot machine")
    async def get_slots(self, ctx):
        await ctx.respond(self.slots.roll(""))

    @bridge.bridge_command(name="chat",
        description="Generate a random bot message")
    async def gen_chat_msg(self, ctx):
        response = self.markov.get_markov_string()
        self.bot.commands_since_new_status += 1
        await ctx.respond(response)
        try:
            await ctx.message.delete()
        except:
            return

    @bridge.bridge_command(name="newvid")
    async def get_newest_youtube_video(self, ctx):
        response = self.youtube.get_most_recent_video(self.bot.account, use_playlist_api=True)
        self.bot.commands_since_new_status += 1
        await ctx.respond(f"Check out the most recent YouTube upload: {response}")

    @bridge.bridge_command(name="youtube")
    async def get_youtube_msg(self, ctx):
        response = self.youtube.get_youtube_com_message(self.bot.account)
        self.bot.commands_since_new_status += 1
        if len(response) > 0:
            await ctx.respond(response)

    @bridge.bridge_command(name="hours",
        description="How many hours of VOD content are available on YouTube?")
    async def get_youtube_hours(self, ctx, playlist: YouTubePlaylists):
        count, duration = self.youtube.get_cache_youtube_playlist_length(self.bot.account, playlist)
        youtube_url = self.youtube.get_youtube_url(self.bot.account)
        await ctx.respond(f"There are {count} videos totalling {int(duration.total_seconds() / 60 / 60)} hours of {playlist} on YouTube: {youtube_url}")

    @bridge.bridge_command(name="ftoc")
    async def farenheit_to_celcius(self, ctx, farenheit: int):
        await ctx.respond(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @bridge.bridge_command(name="ctof")
    async def celcius_to_farenheit(self, ctx, celcius: int):
        await ctx.respond(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")
