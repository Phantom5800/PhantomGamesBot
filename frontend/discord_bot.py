import asyncio
import discord
import json
import os
import random
from time import localtime
import utils.events
from copy import deepcopy
from datetime import datetime, time, timedelta, timezone
from discord.ext import bridge, commands, tasks
from discord.ext.bridge import Bot
from frontend.discord_cogs.discord_commands import PhantomGamesBotCommands
from frontend.discord_cogs.discord_poll import PhantomGamesBotPolls
from frontend.discord_cogs.discord_poll import PhantomGamesBotSimplePolls
from frontend.discord_cogs.discord_schedule import PhantomGamesBotSchedule
from utils.utils import *

# 21:00 UTC = 2:00PM PDT / 1:00PM PST
# trying to check at 1PM regardless of DST
youtube_update_time = time(hour=21 - localtime().tm_isdst, 
                           minute=0,
                           second=0,
                           microsecond=0,
                           tzinfo=timezone.utc)

class PhantomGamesBot(Bot):
    def __init__(self, sharedResources):
        self.account = os.environ['DISCORD_SHARED_API_PROFILE'] # profile to use for shared api's

        # important channel id's that the bot can post messages to
        self.channels = {
            "bot-spam":             956644371426574386,
            "test-channel":         895542329514008578,
            "stream-announcements": 821288412409233409,
            "youtube-uploads":      1095269930892546109,
            "discord-logs":         1098155843326844978,
            "polls":                1115557565082894357,
            "weekly-schedule":      1117682254701932655,
            "twitch-logs":          1294053787400404992
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
            "Paper Mario",
            "WABITR",
            "Bsky/@phantom-games.com",
            "twitch.tv/phantom5800",
            "Zelda: Wand of Gamalon",
            "Visual Studio Code",
            "Mega Man Network Transmission",
            "youtube.com/@PhantomVODs"
        ]
        self.commands_since_new_status = 0

        utils.events.twitchevents.register_events(self)
        self.announce_youtube_vid_task.start()

        # local storage
        self.hype_train_msg = None

    async def set_random_status(self):
        status = self.messages[random.randrange(len(self.messages))]
        print(f"[Status] {status}")
        message = discord.Game(status)
        await self.change_presence(activity=message)

    async def on_ready(self):
        print("=======================================")
        print(f"Discord [{datetime.now()}]: {self.user} is online!")
        self.server = self.get_guild(int(os.environ['DISCORD_SERVER_ID']))
        self.live_role = self.server.get_role(int(os.environ['DISCORD_LIVE_NOW_ID']))
        await self.set_random_status()
        print("=======================================")

    '''
    Handle custom commands.
    '''
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        # only allow custom commands in specific channels
        valid_channel = False
        for channel in self.channels:
            if self.channels[channel] == message.channel.id:
                valid_channel = True
                break
        if valid_channel == False:
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

    async def toggle_live_role(self, member, is_live: bool):
        # apply / remove the "Live Now" role from anyone marked as a "Streamer"
        unrestricted = True
        if unrestricted or member.get_role(int(os.environ['DISCORD_STREAMER_ROLE_ID'])) is not None:
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
        youtube_vid = self.youtube.get_most_recent_video(self.account, use_playlist_api=True)

        if youtube_vid != "":
            last_upload_cache = './commands/resources/last_youtube_post.txt'
            if not os.path.isfile(last_upload_cache):
                open(last_upload_cache, 'w', encoding="utf-8").close()

            with open(last_upload_cache, 'r+', encoding="utf-8") as f:
                last_vid = f.read()
                if last_vid != youtube_vid:
                    print(f"[YouTube] New video. Old: \"{last_vid}\" and Current: \"{youtube_vid}\"")
                    await channel.send(f"{self.roles['youtube-alerts']} {youtube_vid}")
                    f.seek(0)
                    f.write(youtube_vid)
                    f.truncate()
                else:
                    print(f"[YouTube] No new video. Old: \"{last_vid}\" and Current: \"{youtube_vid}\"")

    @tasks.loop(time=youtube_update_time)
    async def announce_youtube_vid_task(self):
        try:
            await self.announce_new_youtube_vid()
        except Exception as err:
            print(f"[Youtube] Failed to get latest video - {err}")

    #####################################################################################################
    # cross bot events
    #####################################################################################################
    async def on_twitch_event_log(self, user:str, msg:str):
        channel = self.get_channel(self.channels["twitch-logs"])
        await channel.send(msg)

    async def on_twitch_stream_event(self, user:str, eventType:utils.events.TwitchEventType, msg:str):
        if eventType == utils.events.TwitchEventType.GoLive:
            channel = self.get_channel(self.channels["stream-announcements"])
            msg = await channel.send(f"{self.roles['stream-notifs']} {msg} https://twitch.tv/{user}")
            await msg.publish()
        elif eventType == utils.events.TwitchEventType.EndStream:
            print(f"[Discord Stream Event] Stream has gone offline - {msg}")
        elif eventType == utils.events.TwitchEventType.HypeTrainStart:
            channel = self.get_channel(self.channels["stream-announcements"])
            self.hype_train_msg = await channel.send(f"{self.roles['stream-notifs']} A hype train has started! https://twitch.tv/{user}")
        elif eventType == utils.events.TwitchEventType.HypeTrainEnd:
            if self.hype_train_msg:
                await self.hype_train_msg.delete()
                self.hype_train_msg = None

def run_discord_bot(eventLoop, sharedResources):
    bot = PhantomGamesBot(sharedResources)
    bot.add_cog(PhantomGamesBotCommands(bot, sharedResources))
    bot.add_cog(PhantomGamesBotPolls(bot))
    #bot.add_cog(PhantomGamesBotSimplePolls(bot))
    bot.add_cog(PhantomGamesBotSchedule(bot, sharedResources))
    async def runBot():
        await bot.start(os.environ['DISCORD_TOKEN'])

    eventLoop.create_task(runBot())
    return bot
