import discord
import json
import os
from copy import deepcopy
from discord.ext import bridge, commands
from enum import IntEnum
from threading import Timer

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
    PapeSettings = 2
    PapeBannedPartner = 3
    TMCSettings = 4

defaultPolls = [
    #########################################################################################
    # Game Selection Polls
    #########################################################################################
    {
        'title': "Bonus Game",
        'active': False,
        'decision': "We're doing an extra rando this week, what should it be?",
        'options': [
            "Minish Cap",
            "Pokémon Crystal"
        ],
        'votes': {}
    },
    {
        'title': "Zelda Game",
        'active': False,
        'decision': "What Zelda Rando do we do this weekend?",
        'options': [
            "Link to the Past",
            "Link's Awakening DX",
            "Minish Cap",
            "Oracle of Seasons",
            "Zelda 1"
        ],
        'votes': {}
    },
    #########################################################################################
    # Pape Rando Settings
    #########################################################################################
    {
        'title': "Pape Setting",
        'active': False,
        'decision': "Which extra setting should we use in Pape Rando?",
        'options': [
            "Coins",
            "Koot + Radio + Dojo",
            "Dungeon Shuffle",
            "Random Starting Location",
            "Jumpless"
        ],
        'votes': {}
    },
    {
        'title': "Banned Partner",
        'active': False,
        'decision': "Ban me from using a partner! This includes all combat and glitches, but they can be used if required for glitchless progression.",
        'options': [
            "Goombario",
            "Kooper",
            "Bombette",
            "Parakarry",
            "Bow",
            "Watt",
            "Sushie",
            "Lakilester"
        ],
        'votes': {}
    },
    #########################################################################################
    # Zelda Rando Settings
    #########################################################################################
    {
        'title': "Minish Cap Setting",
        'active': False,
        'decision': "Which extra setting should we use for a Minish Cap Rando?",
        'options': [
            "Keysanity (Full Keyrings)",
            "Kinstones (Kinstone Bags)",
            "Figurine Hunt",
            "Rupees",
            "Pots + Underwater + Digging",
            "Open World (+No Logic)"
        ],
        'votes': {}
    },
    #########################################################################################
    # Pokémon Rando Settings
    #########################################################################################
    {
        'title': "Crystal Pokémon Randomization",
        'active': False,
        'decision': "Should we add something weird to Pokémon Crystal?",
        'options': [
            "Nothing",
            "Random Stats",
            "Random Move Types",
            "Random Pokémon Types"
        ],
        'votes': {}
    }
]

announcement_base_msg = "These polls are for the Randomizer stream on:"

class PhantomGamesBotPolls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls = defaultPolls
        self.save_timer = None

    async def refresh_poll(self):
        channel = self.bot.get_channel(self.bot.channels["polls"])
        current_poll = 0
        async for message in channel.history(limit=10, oldest_first=True):
            if announcement_base_msg in message.content:
                continue
            if message.author.id == self.bot.user.id:
                if current_poll >= len(self.polls):
                    break
                while self.polls[current_poll]['active'] == False:
                    current_poll += 1
                    if current_poll >= len(self.polls):
                        return
                await message.edit(self.polls[current_poll]['decision'], view=self.build_poll_buttons(self.polls[current_poll], current_poll))
                current_poll += 1

    async def post_new_polls(self, week_date):
        channel = self.bot.get_channel(self.bot.channels["polls"])
        # clear old bot messages and post new ones
        def is_bot_msg(m):
            return m.author.id == self.bot.user.id
        self.clear_votes()
        await channel.purge(limit=10, check=is_bot_msg)
        await channel.send(f"{announcement_base_msg} {week_date}")
        await self.post_current_polls(channel)

    @commands.Cog.listener()
    async def on_ready(self):
        # create a default polls file if one does not exist
        if not os.path.isfile('./commands/resources/discord_polls.json'):
            self.reset_polls()
        self.load_poll_state()
        await self.refresh_poll()

    def save_poll_state(self):
        with open('./commands/resources/discord_polls.json', 'w', encoding='utf-8') as json_file:
            json_str = json.dumps(self.polls, indent=2)
            json_file.write(json_str)

    def load_poll_state(self):
        with open('./commands/resources/discord_polls.json', 'r', encoding='utf-8') as json_file:
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

    def count_votes(self, show_counts):
        vote_results = ""
        for poll in self.polls:
            if poll['active']:
                vote_results += f"{poll['decision']}\n"
                vote_totals = {}
                vote_count = {}
                total_votes = 0
                individual_votes = 0
                for vote in poll['options']:
                    vote_totals[vote] = 0
                    vote_count[vote] = 0
                for vote in poll['votes']:
                    segments = poll['votes'][vote].rsplit(' ', 1)
                    vote_value = int(segments[1][1:-1])

                    # count up the points for each option
                    vote_totals[segments[0]] += vote_value
                    total_votes += vote_value

                    # count up the popular vote
                    vote_count[segments[0]] += 1
                    individual_votes += 1
                for vote in vote_totals:
                    if total_votes > 0:
                        if show_counts:
                            vote_results += f"> {vote}: {int(vote_totals[vote] / total_votes * 100)}% [{vote_count[vote]}/{individual_votes}]\n"
                        else:
                            vote_results += f"> {vote}: {int(vote_totals[vote] / total_votes * 100)}%\n"
                    else:
                        vote_results += f"> {vote}: 0%\n"
        return vote_results

    @bridge.bridge_command(name="pollresults",
        description="Get the results of the current stream polls")    
    async def pollresults(self, ctx, show_vote_counts: bool = False):
        await ctx.respond(self.count_votes(show_vote_counts))

    @bridge.bridge_command(name="togglepoll",
        description="Toggle if a specific poll should be active this week")
    async def togglepoll(self, ctx, poll: PollType):
        self.polls[poll]['active'] = not self.polls[poll]['active']
        await ctx.respond(f"{PollType(poll).name} is now {'enabled' if self.polls[poll]['active'] else 'disabled'}")
        self.save_poll_state()

    @bridge.bridge_command(name="resetpolls",
        description="Reset polls to default state, use this when new polls have been added to the system.")
    async def resetpolls(self, ctx):
        self.reset_polls()
        await ctx.respond("Polls have been reset to default state")

    def build_poll_buttons(self, poll, id):
        view = discord.ui.View(timeout=None)
        for opt in poll['options']:
            button = PollButton(self, id, label=opt)
            view.add_item(button)
        return view

    async def post_current_polls(self, channel):
        polls_posted = 0
        for k,poll in enumerate(self.polls):
            if poll['active']:
                polls_posted += 1
                await channel.send(poll['decision'], view=self.build_poll_buttons(poll, k))
        if polls_posted == 0:
            await channel.send("No polls this week, look forward to hopefully something special on Saturday!")

    @bridge.bridge_command(name="currentpolls",
        description="Get the current stream polls for users to respond to")
    async def currentpolls(self, ctx, week_date: str):
        await self.post_new_polls(week_date)
        #await ctx.respond("Here are the current polls for this week. Reminder that Twitch subs and Discord Server Boosters get extra votes!")
        #await self.post_current_polls(ctx.channel)
        await ctx.respond("Current polls have been updated")
