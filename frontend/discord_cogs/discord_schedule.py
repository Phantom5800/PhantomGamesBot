import discord
import os
import time
from datetime import datetime, timedelta
from discord.ext import bridge, commands
from twitchio.http import Route
from utils.ext_classes import AliasDict

# these categories are hand selected as common options
TwitchCategoryIDs = AliasDict({
    "battle network":   "7542", # BN1 category
    "minish cap":       "5635",
    "paper mario":      "6855",
    "pokemon crystal":  "14543",
    "super mario rpg":  "254327" # or 1675405846
})

# create a set of shorthand aliases for categories
TwitchCategoryIDs.add_alias("battle network", "bn")
TwitchCategoryIDs.add_alias("minish cap", "tmc")
TwitchCategoryIDs.add_alias("paper mario", "pape")
TwitchCategoryIDs.add_alias("pokemon crystal", "crystal")
TwitchCategoryIDs.add_alias("super mario rpg", "smrpg")

class PhantomGamesBotSchedule(commands.Cog):
    def __init__(self, bot, sharedResources):
        self.bot = bot
        self.twitch_bot = sharedResources.twitch_bot

    @bridge.bridge_command(name="weeklyschedule",
        description="Leading any parameter with a | character will mark that day as off with a description.")
    @discord.option("post_twitch",
        description="Whether or not to post these streams to the twitch schedule (default True)")
    async def weeklyschedule(self, ctx, 
        monday: str = None, 
        tuesday: str = None, 
        wednesday: str = None, 
        thursday: str = None, 
        friday: str = None, 
        saturday: str = None, 
        sunday: str = None, 
        post_twitch: bool = True,
        monday_cat: str = None,
        tuesday_cat: str = None,
        wednesday_cat: str = None,
        thursday_cat: str = None,
        friday_cat: str = None,
        saturday_cat: str = None,
        sunday_cat: str = None
    ):
        # figure out the next Monday stream time as a basis
        current = datetime.now()
        current = current.replace(hour=14, minute=0, second=0) # set to 2pm local time
        next_monday_delta = timedelta((7 - current.weekday()) % 7)
        single_day_delta = timedelta(1)
        next_monday = current + next_monday_delta

        # format data into usable structures
        schedule = {
            "Monday": monday,
            "Tuesday": tuesday,
            "Wednesday": wednesday,
            "Thursday": thursday,
            "Friday": friday,
            "Saturday": saturday,
            "Sunday": sunday
        }

        categories = {
            "Monday": monday_cat,
            "Tuesday": tuesday_cat,
            "Wednesday": wednesday_cat,
            "Thursday": thursday_cat,
            "Friday": friday_cat,
            "Saturday": saturday_cat,
            "Sunday": sunday_cat
        }

        # format schedule based on input params
        response = f"{next_monday.strftime('%m/%d')} - {(next_monday + single_day_delta * 6).strftime('%m/%d')}\n\n"
        for i, day in enumerate(schedule):
            response += f"_**{day}**_: "
            if schedule[day] is not None:
                if schedule[day].startswith("|"):
                    response += f"_NO STREAM_ ({schedule[day][1:]})\n"
                else:
                    stream_time = next_monday + single_day_delta * i
                    response += f"{schedule[day]} @ <t:{int(stream_time.timestamp())}:t>\n"

                    # post the day to twitch's schedule
                    if post_twitch:
                        category = None
                        if categories[day] is not None and categories[day].lower() in TwitchCategoryIDs:
                            category = TwitchCategoryIDs[categories[day].lower()]
                        await self.post_single_twitch_schedule(start_time=stream_time, duration="360", title=schedule[day], category_id=category)
            else:
                response += "_NO STREAM_\n"

        # remove old schedule and post the new one
        channel = self.bot.get_channel(self.bot.channels["weekly-schedule"])
        await channel.purge(limit=5)
        await channel.send(response)
        await ctx.respond("Schedule updated", ephemeral=True)

    async def post_single_twitch_schedule(self, start_time: datetime, duration: str, title: str, category_id: str = None):
        # POST https://api.twitch.tv/helix/schedule/segment

        # convert start time to UTC
        start_time = start_time + timedelta(hours=8) # TODO: adjust this for DST

        channel = "phantom5800"
        query=[("broadcaster_id", os.environ.get(f"TWITCH_CHANNEL_ID_{channel}"))]

        body = {
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timezone": "America/Los_Angeles",
            "duration": duration,
            "is_recurring": False,
            "title": title
        }

        # this is technically optional, but would be nice to specify sometimes?
        if category_id is not None:
            body["category_id"] = category_id

        print(body)
        endpoint = Route("POST", "schedule/segment", query=query, body=body, token=os.environ.get(f"TWITCH_CHANNEL_TOKEN_{channel}"))
        await self.twitch_bot._http.request(endpoint)

