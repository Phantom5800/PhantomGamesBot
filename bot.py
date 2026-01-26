import asyncio
import os
from commands.anilist import Anilist
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from commands.src import SrcomApi
from commands.markov import MarkovHandler
from commands.youtube import YouTubeData
from frontend.bsky_bot import run_bsky_bot
from frontend.twitch_bot import run_twitch_bot
from frontend.discord_bot import run_discord_bot
from frontend.gui_interface import run_GUI
from frontend.twitter_bot import run_twitter_bot
from utils.utils import tryParseInt

def run():
    # Shared resources
    sharedResources = lambda:None
    print("========== Custom Commands ==========")
    sharedResources.customCommandHandler = CustomCommands()
    sharedResources.customCommandHandler.load_commands()
    print("============== Quotes ===============")
    sharedResources.quoteHandler = QuoteHandler()
    sharedResources.quoteHandler.load_quotes()
    sharedResources.pastaHandler = QuoteHandler("pasta.json")
    sharedResources.pastaHandler.load_quotes()
    print("=============== SRC =================")
    srcUsers = os.environ['SRC_USER'].split(',')
    sharedResources.srcHandler = SrcomApi(srcUsers[0], False)
    print("============= Markov ================")
    sharedResources.markovHandler = MarkovHandler()
    print("============= YouTube ================")
    sharedResources.youtube = YouTubeData()
    print("=====================================")
    sharedResources.anilist = Anilist()

    # twitch bot acts as a master bot that appends other bot event loops to its own
    sharedResources.twitch_bot = run_twitch_bot(sharedResources)

    # bsky bot for posting / deleting go live notifications
    bsky_handle = os.environ.get("BSKY_HANDLE")
    bsky_pw = os.environ.get("BSKY_PW")
    if bsky_handle and bsky_pw:
        sharedResources.bsky_bot = run_bsky_bot(bsky_handle, bsky_pw)

    # verify and run discord bot
    # TODO: better verification, but empty is probably good enough
    if os.environ['DISCORD_TOKEN'] is not None and len(os.environ['DISCORD_TOKEN']) > 0:
        sharedResources.discord_bot = run_discord_bot(sharedResources.twitch_bot.loop, sharedResources)

    # verify that twitter credentials are configured
    if os.environ['TWITTER_CONSUMER_KEY'] is not None and len(os.environ['TWITTER_CONSUMER_KEY']) > 0:
        run_twitter_bot(sharedResources.twitch_bot.loop, sharedResources.markovHandler)

    # load the GUI window
    if tryParseInt(os.environ.get('ENABLE_GUI', 1)):
        run_GUI(sharedResources.twitch_bot.loop, sharedResources)

    sharedResources.twitch_bot.run()

if __name__ == "__main__":
    run()
