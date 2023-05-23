import asyncio
from copy import deepcopy
from enum import IntEnum
from datetime import datetime, timedelta, timezone
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
    #async def on_presence_update(self, before, after):
        # check to see when people go live or go offline
        # if isinstance(before.activity, discord.Streaming) and not isinstance(after.activity, discord.Streaming):
        #     print(f"{before.display_name} was streaming, but isn't now")
        # elif not isinstance(before.activity, discord.Streaming) and isinstance(after.activity, discord.Streaming):
        #     print(f"{before.display_name} is now streaming!")

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
            else:
                print(f"[YouTube] No new video. Old: \"{last_vid}\" and Current: \"{youtube_vid}\"")
    
    async def announce_youtube_vid_task(self):
        channel = self.get_channel(self.channels["youtube-uploads"])
        while True:
            now = datetime.now(timezone.utc)

            last_post = (await channel.history(limit=1).flatten())[0]
            last_post_time = last_post.created_at
            time_since_last_post = now - last_post_time

            if time_since_last_post.total_seconds() >= 12 * 60 * 60:
                try:
                    await self.announce_new_youtube_vid()
                except:
                    print("[Youtube] Rate limit reached for the day")

            # 19:00 UTC = noon PT
            today = now.replace(hour = 19, minute = 10, second = 0, microsecond = 0)
            tomorrow = today
            if tomorrow < now:
                tomorrow += timedelta(days = 1)
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
        brief="Roll the slot machine")
    async def get_slots(self, ctx):
        await ctx.respond(self.slots.roll(""))

    @bridge.bridge_command(name="chat",
        brief="Generate a random bot message")
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

    @bridge.bridge_command(name="hours")
    async def get_youtube_hours(self, ctx):
        count, duration = self.youtube.get_cache_youtube_playlist_length(self.bot.account, "Paper Mario Randomizers")
        youtube_url = self.youtube.get_youtube_url(self.bot.account)
        await ctx.respond(f"There are {count} videos totalling {int(duration.total_seconds() / 60 / 60)} hours of Paper Mario Randomizer on YouTube: {youtube_url}")

    @bridge.bridge_command(name="ftoc")
    async def farenheit_to_celcius(self, ctx, farenheit: int):
        await ctx.respond(f"{farenheit}°F = {str(round((farenheit - 32) * 5 / 9, 2))}°C")

    @bridge.bridge_command(name="ctof")
    async def celcius_to_farenheit(self, ctx, celcius: int):
        await ctx.respond(f"{celcius}°C = {str(round(celcius * 9 / 5 + 32, 2))}°F")

class PollButton(discord.ui.Button):
    def __init__(self, poll_manager, poll_id: int, label=None, emoji=None, row=None):
        super().__init__(label=label, emoji=emoji, row=row)
        self.manager = poll_manager
        self.id = poll_id

    async def callback(self, interaction):
        self.manager.update_votes(self.id, self.label, interaction.user)
        await interaction.response.defer()

class PollType(IntEnum):
    BonusRandomizer = 0
    ZeldaRando = 1
    PapeRando = 2

class PhantomGamesBotPolls(commands.Cog):
    def __init__(self):
        self.polls = [
            {
                'active': True,
                'decision': "We're doing an extra rando this week, what should it be?",
                'options': [
                    "Minish Cap",
                    "Pokémon Crystal"
                ],
                'votes': {}
            },
            {
                'active': True,
                'decision': "What Zelda Rando do we do this weekend?",
                'options': [
                    "Link to the Past",
                    "Minish Cap",
                    "Oracle of Seasons",
                    "Zelda 1"
                ],
                'votes': {}
            },
            {
                'active': True,
                'decision': "Which extra setting should we use in Pape Rando?",
                'options': [
                    "Coins",
                    "Koopa Koot",
                    "Dungeon Shuffle",
                    "Random Starting Location",
                    "Jumpless"
                ],
                'votes': {}
            }
        ]

    def update_votes(self, id: int, choice: str, user):
        vote_value = 1
        for role in user.roles:
            # don't count the streamers vote lol
            if role.name == "Phantom":
                vote_value = 0
                break
            # one extra vote per tier of twitch sub
            if "Twitch Subscriber: Tier" in role.name:
                vote_value += int(role.name[-1])
            # one extra vote for boosting the discord server
            if role.name == "Server Booster":
                vote_value += 1

        self.polls[id]['votes'][user.id] = f"{choice} [{vote_value}]"

    def count_votes(self):
        vote_results = ""
        for poll in self.polls:
            if poll['active']:
                vote_results += f"{poll['decision']}\n"
                vote_totals = {}
                total_votes = 0
                for vote in poll['options']:
                    vote_totals[vote] = 0
                for vote in poll['votes']:
                    segments = vote.split(' ')
                    vote_value = int(segments[1][1:-1])
                    vote_totals[segments[0]] += vote_value
                    total_votes += vote_value
                for vote in vote_totals:
                    if total_votes > 0:
                        vote_results += f"> {vote}: {int(vote_totals[vote] / total_votes * 100)}%\n"
                    else:
                        vote_results += f"> {vote}: 0%\n"
        return vote_results

    @bridge.bridge_command(name="pollresults",
        brief="Get the results of the current stream polls")    
    async def pollresults(self, ctx):
        if ctx.author.id == int(os.environ.get("DISCORD_STREAMER_ID")):
            await ctx.respond(self.count_votes())
        else:
            await ctx.respond("You don't have permission to see poll results")

    @bridge.bridge_command(name="togglepoll",
        brief="Toggle if a specific poll should be active this week")
    async def togglepoll(self, ctx, poll: PollType):
        if ctx.author.id == int(os.environ.get("DISCORD_STREAMER_ID")):
            self.polls[poll]['active'] = not self.polls[poll]['active']
            await ctx.respond(f"{PollType(poll).name} is now {'enabled' if self.polls[poll]['active'] else 'disabled'}")
        else:
            await ctx.respond("You don't have permission to set the poll")

    # Polls need to only allow users to vote once, selecting another option changes their vote
    # Twitch subs count for an extra vote per tier
    # Need to be able to reconnect to messages when the bot restarts
    @bridge.bridge_command(name="currentpolls",
        brief="Get the current stream polls for users to respond to")
    async def currentpolls(self, ctx):
        await ctx.respond("Here are the current polls for this week. Reminder that Twitch subs and Discord Server Boosters get extra votes!")
        for k,poll in enumerate(self.polls):
            if poll['active']:
                view = discord.ui.View()
                for opt in poll['options']:
                    button = PollButton(self, k, label=opt)
                    view.add_item(button)
                await ctx.channel.send(poll['decision'], view=view)

def run_discord_bot(eventLoop, sharedResources):
    bot = PhantomGamesBot(sharedResources)
    bot.add_cog(PhantomGamesBotModule(bot, sharedResources))
    bot.add_cog(PhantomGamesBotPolls())
    async def runBot():
        await bot.start(os.environ['DISCORD_TOKEN'])

    eventLoop.create_task(runBot())
