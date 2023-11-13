import discord
import time
from datetime import datetime, timedelta
from discord.ext import bridge, commands

class PhantomGamesBotSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command(name="weeklyschedule",
        description="Leading any parameter with a | character will mark that day as off with a description.")
    async def weeklyschedule(self, ctx, monday: str = None, tuesday: str = None, wednesday: str = None, thursday: str = None, friday: str = None, saturday: str = None, sunday: str = None):
        current = datetime.now()
        current = current.replace(hour=14, minute=0) # set to 2pm local time
        next_monday_delta = timedelta((7 - current.weekday()) % 7)
        single_day_delta = timedelta(1)
        next_monday = current + next_monday_delta

        schedule = {
            "Monday": monday,
            "Tuesday": tuesday,
            "Wednesday": wednesday,
            "Thursday": thursday,
            "Friday": friday,
            "Saturday": saturday,
            "Sunday": sunday
        }

        response = f"{next_monday.strftime('%m/%d')} - {(next_monday + single_day_delta * 6).strftime('%m/%d')}\n\n"
        for i, day in enumerate(schedule):
            response += f"_**{day}**_: "
            if schedule[day] is not None:
                if schedule[day].startswith("|"):
                    response += f"_NO STREAM_ ({schedule[day][1:]})\n"
                else:
                    response += f"{schedule[day]} @ <t:{int((next_monday + single_day_delta * i).timestamp())}:t>\n"
            else:
                response += "_NO STREAM_\n"

        channel = self.bot.get_channel(self.bot.channels["weekly-schedule"])
        await channel.purge(limit=5)
        await channel.send(response)
        await ctx.respond("Schedule updated", ephemeral=True)
