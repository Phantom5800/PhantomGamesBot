import asyncio
import os
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from commands.src import SrcomApi
from commands.markov import MarkovHandler
from frontend.twitch_bot import run_twitch_bot
from frontend.discord_bot import run_discord_bot
from frontend.twitter_bot import run_twitter_bot

if __name__ == "__main__":
    # Shared resources
    customCommandHandler = CustomCommands()
    quoteHandler = QuoteHandler()
    print("========== Custom Commands ==========")
    customCommandHandler.load_commands()
    print("============== Quotes ===============")
    quoteHandler.load_quotes()
    print("=============== SRC =================")
    srcUsers = os.environ['SRC_USER'].split(',')
    srcHandler = SrcomApi(srcUsers[0])
    print("============= Markov ================")
    markovHandler = MarkovHandler()
    print("=====================================")

    sharedResources = lambda:None
    sharedResources.customCommandHandler = customCommandHandler
    sharedResources.quoteHandler         = quoteHandler
    sharedResources.srcHandler           = srcHandler
    sharedResources.markovHandler        = markovHandler

    # twitch bot acts as a master bot that appends other bot event loops to its own
    masterBot = run_twitch_bot(sharedResources)

    # verify and run discord bot
    # TODO: better verification, but empty is probably good enough
    if os.environ['DISCORD_TOKEN'] is not None and len(os.environ['DISCORD_TOKEN']) > 0:
        run_discord_bot(masterBot.loop, sharedResources)

    # verify that twitter credentials are configured
    if os.environ['TWITTER_CONSUMER_KEY'] is not None and len(os.environ['TWITTER_CONSUMER_KEY']) > 0:
        run_twitter_bot(masterBot.loop, markovHandler)

    masterBot.run()
