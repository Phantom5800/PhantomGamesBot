import discord
import json
import os
from copy import deepcopy
from datetime import datetime, timedelta
from discord.ext import bridge, commands
from enum import IntEnum
from frontend.discord_cogs.discord_default_polls import defaultPolls
from threading import Timer

class PollButton(discord.ui.Button):
    def __init__(self, poll_manager, poll_id: int, label=None, emoji=None, row=None):
        super().__init__(label=label, custom_id=label, emoji=emoji, row=row)
        self.manager = poll_manager
        self.id = poll_id

    async def callback(self, interaction):
        await self.manager.update_votes(self.id, self.label, interaction.user)
        await interaction.response.send_message(f"Voted for {self.label}", ephemeral=True)

class PollToggleButton(discord.ui.Button):
    def __init__(self, parent, poll_manager, poll_id: int, label=None, emoji=None):
        row = poll_manager.polls[poll_id]['menuRow']
        super().__init__(label=label, custom_id=label, emoji=emoji, row=row)
        self.id = poll_id
        self.style = discord.ButtonStyle.green if poll_manager.polls[poll_id]['active'] else discord.ButtonStyle.red

class PollToggleMenu(discord.ui.View):
    def __init__(self, poll_manager):
        super().__init__()

        # button for posting current poll for Saturday only
        post_button = discord.ui.Button(label="Post Saturday Polls", custom_id="Post Polls 1", row=0)
        post_button.style = discord.ButtonStyle.primary
        async def post_callback(interaction, poll_manager=poll_manager):
            await poll_manager.post_weekly_polls(multiple_days=False)
            await interaction.response.send_message("Current polls have been updated", ephemeral=True)
        post_button.callback = post_callback
        self.add_item(post_button)

        # button for posting current poll for Saturday and Sunday
        post_button2 = discord.ui.Button(label="Post Weekend Polls", custom_id="Post Polls 2", row=0)
        post_button2.style = discord.ButtonStyle.primary
        async def post_callback2(interaction, poll_manager=poll_manager):
            await poll_manager.post_weekly_polls(multiple_days=True)
            await interaction.response.send_message("Current polls have been updated", ephemeral=True)
        post_button2.callback = post_callback2
        self.add_item(post_button2)

        # button for showing current results
        results_button = discord.ui.Button(label="Show Results", custom_id="Show Results", row=0)
        results_button.style = discord.ButtonStyle.primary
        async def results_callback(interaction, poll_manager=poll_manager):
            await interaction.response.send_message(poll_manager.count_votes(True), ephemeral=True)
        results_button.callback = results_callback
        self.add_item(results_button)

        # create a button for each poll in the set
        for k,poll in enumerate(poll_manager.polls):
            button = PollToggleButton(self, poll_manager, k, label=poll['title'])
            async def button_callback(interaction, button=button, poll_manager=poll_manager):
                button.style = discord.ButtonStyle.red if poll_manager.polls[button.id]['active'] else discord.ButtonStyle.green
                interaction = await interaction.response.edit_message(view=self)
                await poll_manager.togglepoll(button.id)
            button.callback = button_callback

            self.add_item(button)

    async def post_menu(self, ctx):
        self.message = await ctx.respond(view=self)

    async def on_timeout(self):
        await self.message.delete_original_response()

class PollType(IntEnum):
    BonusRandomizer = 0
    ZeldaRando = 1
    PapeSettings = 2
    PapeBannedSetting = 3
    PapeBannedPartner = 4
    TMCSettings = 5

announcement_base_msg = "<@&1171521685527208007> New polls ending on:"

class PhantomGamesBotPolls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls = defaultPolls

    # edit the current weekly poll on a bot start to refresh buttons
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

    # delete the old polls and post a new set
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
            elif "Twitch Subscriber: Tier" in role.name:
                vote_value += int(role.name[-1])
            # one extra vote for boosting the discord server
            elif role.name == "Server Booster":
                vote_value += 1
            # youtube member tiers, nothing extra for base supporter
            elif "YouTube Member" in role.name:
                # 1 extra vote for $4.99 premium tier
                if "Premium" in role.name:
                    vote_value += 1
                # 2 extra votes for $9.99 gold tier
                elif "Gold" in role.name:
                    vote_value += 2

        self.polls[id]['votes'][str(user.id)] = f"{choice} [{vote_value}]"
        self.save_poll_state()

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

    async def togglepoll(self, poll: int):
        self.polls[poll]['active'] = not self.polls[poll]['active']
        self.save_poll_state()

    @bridge.bridge_command(name="pollselectmenu",
        description="Display the menu for toggling which polls are enabled")
    async def pollselectmenu(self, ctx):
        await PollToggleMenu(self).post_menu(ctx)

    @bridge.bridge_command(name="showpollresults")
    async def showpollresults(self, ctx):
        await ctx.respond(self.count_votes(False), ephemeral=True)

    @bridge.bridge_command(name="resetpolls",
        description="Reset all polls to default states")
    async def resetpolls(self, ctx):
        self.reset_polls()
        await ctx.respond("Polls have been reset")

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
            await channel.send("No polls this week! See <#1117682254701932655> for details on what is happening this week!")

    async def post_weekly_polls(self, multiple_days: bool):
        current = datetime.now()
        delta = timedelta((12 - current.weekday()) % 7) # delta time to the next saturday from current time
        first_day = current + delta
        week_date = first_day.strftime("%B %d")
        if multiple_days:
            week_date += f" and {(first_day + timedelta(days=1)).strftime('%d')}"
        await self.post_new_polls(week_date)
