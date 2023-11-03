import discord
import time
from datetime import datetime, timedelta
from discord.ext import bridge, commands

class PhantomGamesBotSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command(name="weeklyschedule")
    async def weeklyschedule(self, ctx, monday: str = None, tuesday: str = None, wednesday: str = None, thursday: str = None, friday: str = None, saturday: str = None, sunday: str = None):
        current = datetime.now()
        current = current.replace(hour=14, minute=0) # set to 2pm local time
        next_monday_delta = timedelta((7 - current.weekday()) % 7)
        single_day_delta = timedelta(1)
        next_monday = current + next_monday_delta

        schedule = [
            monday,
            tuesday,
            wednesday,
            thursday,
            friday,
            saturday,
            sunday
        ]

        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        response = ""
        for i in range(0, len(schedule)):
            response += f"_**{days[i]}**_: "
            if schedule[i] is not None:
                response += f"{schedule[i]} @ <t:{int((next_monday + single_day_delta * i).timestamp())}:t>\n"
            else:
                response += "_NO STREAM_\n"

        channel = self.bot.get_channel(self.bot.channels["weekly-schedule"])
        await channel.purge(limit=5)
        await channel.send(response)
        await ctx.respond("Schedule updated", ephemeral=True)
