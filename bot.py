import asyncio
import os
from commands.anilist import Anilist
from commands.custom_commands import CustomCommands
from commands.goals import Goals
from commands.quotes import QuoteHandler
from commands.src import SrcomApi
from commands.markov import MarkovHandler
from commands.youtube import YouTubeData
from frontend.twitch_bot import run_twitch_bot
from frontend.discord_bot import run_discord_bot
from frontend.twitter_bot import run_twitter_bot

def run():
    # Shared resources
    sharedResources = lambda:None
    print("========== Custom Commands ==========")
    sharedResources.customCommandHandler = CustomCommands()
    sharedResources.customCommandHandler.load_commands()
    print("============== Quotes ===============")
    sharedResources.quoteHandler = QuoteHandler()
    sharedResources.quoteHandler.load_quotes()
    print("=============== SRC =================")
    srcUsers = os.environ['SRC_USER'].split(',')
    sharedResources.srcHandler = SrcomApi(srcUsers[0])
    print("============= Markov ================")
    sharedResources.markovHandler = MarkovHandler()
    print("============= YouTube ================")
    sharedResources.youtube = YouTubeData()
    print("=====================================")
    sharedResources.anilist = Anilist()
    sharedResources.goals = Goals("phantom5800")
    sharedResources.goals.load_goals()

    # twitch bot acts as a master bot that appends other bot event loops to its own
    sharedResources.twitch_bot = run_twitch_bot(sharedResources)

    # verify and run discord bot
    # TODO: better verification, but empty is probably good enough
    if os.environ['DISCORD_TOKEN'] is not None and len(os.environ['DISCORD_TOKEN']) > 0:
        sharedResources.discord_bot = run_discord_bot(sharedResources.twitch_bot.loop, sharedResources)

    # verify that twitter credentials are configured
    if os.environ['TWITTER_CONSUMER_KEY'] is not None and len(os.environ['TWITTER_CONSUMER_KEY']) > 0:
        run_twitter_bot(sharedResources.twitch_bot.loop, sharedResources.markovHandler)

    sharedResources.twitch_bot.run()

if __name__ == "__main__":
    run()
