import discord
import os
import time
from datetime import datetime, timedelta
from discord.ext import bridge, commands
from twitchio.http import Route
from utils.ext_classes import AliasDict
from utils.utils import get_twitch_user

LocalStartTimeHours = 10 # 10am

# these categories are hand selected as common options
TwitchCategoryIDs = AliasDict({
    "battle network":           "7542", # BN1 category
    "kirby 64":                 "15681",
    "links awakening":          "3337", # 959980201 is the LAS category
    "link to the past":         "9435",
    "minish cap":               "5635",
    "ocarina of time":          "11557",
    "okami":                    "18791",
    "paper mario":              "18231",
    "pokemon colosseum":        "11879",
    "pokemon crystal":          "14543",
    "pokemon emerald":          "10609",
    "retro":                    "27284",
    "shadow the hedgehog":      "17794",
    "sonic adventure":          "7195",
    "sonic adventure 2":        "1386697379",
    "super mario rpg":          "1675405846",
    "super smash bros brawl":   "18833",
    "the thousand-year door":   "2029972667", # 6855 is the original
    "twilight princess":        "17828"
})

# create a set of shorthand aliases for categories
TwitchCategoryIDs.add_alias("battle network", "bn")
TwitchCategoryIDs.add_alias("link to the past", "alttp")
TwitchCategoryIDs.add_alias("link to the past", "lttp")
TwitchCategoryIDs.add_alias("link to the past", "z3")
TwitchCategoryIDs.add_alias("links awakening", "la")
TwitchCategoryIDs.add_alias("links awakening", "ladx")
TwitchCategoryIDs.add_alias("minish cap", "tmc")
TwitchCategoryIDs.add_alias("ocarina of time", "oot")
TwitchCategoryIDs.add_alias("paper mario", "pape")
TwitchCategoryIDs.add_alias("pokemon colosseum", "colo")
TwitchCategoryIDs.add_alias("pokemon colosseum", "colosseum")
TwitchCategoryIDs.add_alias("pokemon crystal", "crystal")
TwitchCategoryIDs.add_alias("pokemon emerald", "emerald")
TwitchCategoryIDs.add_alias("shadow the hedgehog", "shadow")
TwitchCategoryIDs.add_alias("sonic adventure", "sa1")
TwitchCategoryIDs.add_alias("sonic adventure 2", "sa2")
TwitchCategoryIDs.add_alias("super mario rpg", "smrpg")
TwitchCategoryIDs.add_alias("super smash bros brawl", "brawl")
TwitchCategoryIDs.add_alias("the thousand-year door", "ttyd")
TwitchCategoryIDs.add_alias("twilight princess", "tp")

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
        sunday_cat: str = None,
        monday_offset: int = 0,
        tuesday_offset: int = 0,
        wednesday_offset: int = 0,
        thursday_offset: int = 0,
        friday_offset: int = 0,
        saturday_offset: int = 0,
        sunday_offset: int = 0
    ):
        # defer because this is gonna take a bit to process
        await ctx.defer(ephemeral=True)

        # figure out the next Monday stream time as a basis
        current = datetime.now()
        current = current.replace(hour=LocalStartTimeHours, minute=0, second=0) # set to 10am local time
        next_monday_delta = timedelta((7 - current.weekday()) % 7)
        single_day_delta = timedelta(days=1)
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

        offsets = {
            "Monday": monday_offset,
            "Tuesday": tuesday_offset,
            "Wednesday": wednesday_offset,
            "Thursday": thursday_offset,
            "Friday": friday_offset,
            "Saturday": saturday_offset,
            "Sunday": sunday_offset
        }

        # format schedule based on input params
        response = f"{next_monday.strftime('%m/%d')} - {(next_monday + single_day_delta * 6).strftime('%m/%d')}\n\n"
        for i, day in enumerate(schedule):
            response += f"_**{day}**_: "
            if schedule[day] is not None:
                if schedule[day].startswith("|"):
                    response += f"_NO STREAM_ ({schedule[day][1:]})\n"
                else:
                    offset = timedelta(hours=offsets[day])
                    stream_time = next_monday + single_day_delta * i + offset
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
        start_time = start_time + timedelta(hours=(8 - time.localtime().tm_isdst))

        channel = "phantom5800"
        twitch_channel = await get_twitch_user(self.twitch_bot, channel)
        query=[("broadcaster_id", twitch_channel.user.id)]

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

