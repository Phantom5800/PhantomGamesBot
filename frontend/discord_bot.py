import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from enum import IntEnum
import json
import os
from threading import Timer
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
            "discord-logs":         1098155843326844978,
            "polls":                1115557565082894357
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
        self.server = self.get_guild(int(os.environ['DISCORD_SERVER_ID']))
        self.live_role = self.server.get_role(int(os.environ['DISCORD_LIVE_NOW_ID']))

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

    async def toggle_live_role(self, member, is_live=False):
        # apply / remove the "Live Now" role from anyone marked as a "Streamer"
        if True or member.get_role(int(os.environ['DISCORD_STREAMER_ROLE_ID'])) is not None:
            if is_live:
                await member.add_roles(self.live_role)
            else:
                await member.remove_roles(self.live_role)

    '''
    Handle anything that needs to be updated when a user's discord status changes.
    '''
    async def on_presence_update(self, before, after):
        # check to see when people go live or go offline
        if isinstance(before.activity, discord.Streaming) and not isinstance(after.activity, discord.Streaming):
            await self.toggle_live_role(before, is_live=False)
        elif not isinstance(before.activity, discord.Streaming) and isinstance(after.activity, discord.Streaming):
            await self.toggle_live_role(before, is_live=True)

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
        super().__init__(label=label, custom_id=label, emoji=emoji, row=row)
        self.manager = poll_manager
        self.id = poll_id

    async def callback(self, interaction):
        await self.manager.update_votes(self.id, self.label, interaction.user)
        await interaction.response.send_message(f"Voted for {self.label}", ephemeral=True)

class PollType(IntEnum):
    BonusRandomizer = 0
    ZeldaRando = 1
    PapeRando = 2
    PapeStarHunt = 3

defaultPolls = [
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
    },
    {
        'active': True,
        'decision': "Power Star Hunt or Boss Rush in Pape Rando?",
        'options': [
            "Power Star Hunt",
            "Boss Rush"
        ],
        'votes': {}
    }
]

class PhantomGamesBotPolls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls = defaultPolls
        self.save_timer = None

    async def refresh_poll(self):
        channel = self.bot.get_channel(self.bot.channels["polls"])
        current_poll = 0
        async for message in channel.history(limit=10, oldest_first=True):
            if message.author.id == self.bot.user.id:
                if current_poll >= len(self.polls):
                    break
                while self.polls[current_poll]['active'] == False:
                    current_poll += 1
                    if current_poll >= len(self.polls):
                        break
                await message.edit(self.polls[current_poll]['decision'], view=self.build_poll_buttons(self.polls[current_poll], current_poll))
                current_poll += 1

    async def post_new_polls(self):
        channel = self.bot.get_channel(self.bot.channels["polls"])
        # clear old bot messages and post new ones
        def is_bot_msg(m):
            return m.author.id == self.bot.user.id
        self.clear_votes()
        await channel.purge(limit=10, check=is_bot_msg)
        await self.post_current_polls(channel)

    @commands.Cog.listener()
    async def on_ready(self):
        self.load_poll_state()
        await self.refresh_poll()

    def save_poll_state(self):
        with open(f'./commands/resources/discord_polls.json', 'w', encoding='utf-8') as json_file:
            json_str = json.dumps(self.polls, indent=2)
            json_file.write(json_str)

    def load_poll_state(self):
        with open(f'./commands/resources/discord_polls.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            self.polls = deepcopy(data)

    def reset_polls(self):
        self.polls = defaultPolls
        self.save_poll_state()

    def clear_votes(self):
        for poll in self.polls:
            poll['votes'] = {}
        self.save_poll_state()

    async def update_votes(self, id: int, choice: str, user):
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

        self.polls[id]['votes'][str(user.id)] = f"{choice} [{vote_value}]"
        if self.save_timer is not None:
            self.save_timer.cancel()

        def save_state():
            self.save_poll_state()
            self.save_timer = None
        self.save_timer = Timer(600, save_state)
        self.save_timer.start()

        # log new votes
        print(f"[Vote] {user.id}: {choice} [{vote_value}]")

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
                    segments = poll['votes'][vote].rsplit(' ', 1)
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
        await ctx.respond(self.count_votes())

    @bridge.bridge_command(name="togglepoll",
        brief="Toggle if a specific poll should be active this week")
    async def togglepoll(self, ctx, poll: PollType):
        self.polls[poll]['active'] = not self.polls[poll]['active']
        await ctx.respond(f"{PollType(poll).name} is now {'enabled' if self.polls[poll]['active'] else 'disabled'}")
        self.save_poll_state()

    def build_poll_buttons(self, poll, id):
        view = discord.ui.View(timeout=None)
        for opt in poll['options']:
            button = PollButton(self, id, label=opt)
            view.add_item(button)
        return view

    async def post_current_polls(self, channel):
        for k,poll in enumerate(self.polls):
            if poll['active']:
                await channel.send(poll['decision'], view=self.build_poll_buttons(poll, k))

    @bridge.bridge_command(name="currentpolls",
        brief="Get the current stream polls for users to respond to")
    async def currentpolls(self, ctx):
        await self.post_new_polls()
        #await ctx.respond("Here are the current polls for this week. Reminder that Twitch subs and Discord Server Boosters get extra votes!")
        #await self.post_current_polls(ctx.channel)
        await ctx.respond("Current polls have been updated")

def run_discord_bot(eventLoop, sharedResources):
    bot = PhantomGamesBot(sharedResources)
    bot.add_cog(PhantomGamesBotModule(bot, sharedResources))
    bot.add_cog(PhantomGamesBotPolls(bot))
    async def runBot():
        await bot.start(os.environ['DISCORD_TOKEN'])

    eventLoop.create_task(runBot())
