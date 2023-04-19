import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
import discord
import random
from discord.ext import bridge, commands
from commands.slots import Slots
from commands.slots import SlotsMode
from utils.utils import *

class PhantomGamesBot(bridge.Bot):
    def __init__(self, sharedResources):
        self.account = os.environ['DISCORD_SHARED_API_PROFILE'] # profile to use for shared api's

        # important channel id's that the bot can post messages to
        self.channels = {
            "bot-spam":             956644371426574386,
            "test-channel":         895542329514008578,
            "stream-announcements": 821288412409233409,
            "youtube-uploads":      1095269930892546109,
            "discord-logs":         1098155843326844978
        }

        self.roles = {
            "stream-notifs":    '<@&916759082206134362>',
            "youtube-alerts":   '<@&1095269470295044128>'
        }

        # initialize discord API hooks
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        super().__init__(
            command_prefix=os.environ['BOT_PREFIX'],
            intents=intents
        )

        # cache important shared resources
        self.custom = sharedResources.customCommandHandler
        self.youtube = sharedResources.youtube

        # status messages
        self.messages = [
            "Responding to !speed",
            "!boris",
            "Paper Mario Randomizer",
            "WABITR",
            "Twitter",
            "twitch.tv/phantom5800",
            "Zelda: Wand of Gamalon",
            "Visual Studio Code",
            "Mega Man Network Transmission",
            "youtube.com/@PhantomVODs"
        ]
        self.commands_since_new_status = 0

    async def set_random_status(self):
        status = self.messages[random.randrange(len(self.messages))]
        print(f"[Status] {status}")
        message = discord.Game(status)
        await self.change_presence(activity=message)

    async def on_ready(self):
        print("=======================================")
        print(f"Discord [{datetime.now()}]: {self.user} is online!")
        self.loop.create_task(self.announce_youtube_vid_task())
        await self.set_random_status()
        print("=======================================")

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
                response = self.custom.parse_custom_command(command, self.account)
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
    
    async def on_member_join(self, member):
        channel = self.get_channel(self.channels["discord-logs"])
        await channel.send(f"New discord member: {member.mention} {member.name}")

    async def on_member_remove(self, member):
        channel = self.get_channel(self.channels["discord-logs"])
        await channel.send(f"User left discord: {member.mention} {member.name}")

    '''
    Handle anything that needs to be updated when a user's discord status changes.
    '''
    async def on_presence_update(self, before, after):
        # check to see when people go live or go offline
        if isinstance(before.activity, discord.Streaming) and not isinstance(after.activity, discord.Streaming):
            print(f"{before.display_name} was streaming, but isn't now")
        elif not isinstance(before.activity, discord.Streaming) and isinstance(after.activity, discord.Streaming):
            print(f"{before.display_name} is now streaming!")

    '''
    Periodically call this function to post the latest video in youtube-uploads when a new one is posted.
    '''
    async def announce_new_youtube_vid(self):
        channel = self.get_channel(self.channels["youtube-uploads"])
        youtube_vid = self.youtube.get_most_recent_video(self.account)

        with open('./commands/resources/last_youtube_post.txt', 'r+', encoding="utf-8") as f:
            last_vid = f.read()
            if last_vid != youtube_vid:
                await channel.send(f"{self.roles['youtube-alerts']} {youtube_vid}")
                f.seek(0)
                f.write(youtube_vid)
                f.truncate()
    
    async def announce_youtube_vid_task(self):
        while True:
            await self.announce_new_youtube_vid()

            now = datetime.now()
            today = now.replace(hour = 12, minute = 10, second = 0, microsecond = 0)
            tomorrow = today + timedelta(days = 1)
            seconds = (tomorrow - now).total_seconds()
            print(f"[Youtube {now}] Checking for new youtube video in {seconds} seconds")

            await asyncio.sleep(seconds)

'''
Unlike twitchio, discord bot is unable to embed commands directly, and requires cogs.
'''
class PhantomGamesBotModule(commands.Cog):
    def __init__(self, bot: PhantomGamesBot, sharedResources):
        self.bot = bot
        self.quotes = sharedResources.quoteHandler
        self.speedrun = sharedResources.srcHandler
        self.markov = sharedResources.markovHandler
        self.anilist = sharedResources.anilist
        self.youtube = sharedResources.youtube
        self.slots = Slots(SlotsMode.DISCORD)
    
    @bridge.bridge_command(brief="Get a link to the bot's github.", help="Get a link to the bot's github.")
    async def bot(self, ctx: commands.Context):
        await ctx.respond("Hey! I am a custom chatbot written in Python, my source code is available at: https://github.com/Phantom5800/PhantomGamesBot")

    @bridge.bridge_command(name="commands", 
        brief="Get a list custom commands created on twitch.",
        help="Get a list of all basic response commands. These commands are all added by moderators on twitch.")
    async def get_commands(self, ctx):
        command_list = []
        command_list.extend(self.bot.custom.get_command_list(self.account))
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
            await ctx.respond(self.quotes.pick_specific_quote(str(self.quotes.num_quotes() - 1), self.bot.account))
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

    @bridge.bridge_command(name="newvid")
    async def get_newest_youtube_video(self, ctx):
        response = self.youtube.get_most_recent_video(self.bot.account)
        self.bot.commands_since_new_status += 1
        await ctx.respond(f"Check out the most recent YouTube upload: {response}")

    @bridge.bridge_command(name="youtube")
    async def get_youtube_msg(self, ctx):
        response = self.youtube.get_youtube_com_message(self.bot.account)
        self.bot.commands_since_new_status += 1
        if len(response) > 0:
            await ctx.respond(response)

    @bridge.bridge_command(name="ftoc")
    async def farenheit_to_celcius(self, ctx, farenheit: int):
        await ctx.respond(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @bridge.bridge_command(name="ctof")
    async def celcius_to_farenheit(self, ctx, celcius: int):
        await ctx.respond(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")

def run_discord_bot(eventLoop, sharedResources):
    bot = PhantomGamesBot(sharedResources)
    bot.add_cog(PhantomGamesBotModule(bot, sharedResources))
    async def runBot():
        await bot.start(os.environ['DISCORD_TOKEN'])

    eventLoop.create_task(runBot())
