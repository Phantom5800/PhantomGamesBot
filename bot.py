from commands import *
from frontend import *
from utils import getenv, getenv_int

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
    sharedResources.srcHandler = SrcomApi()
    print("============= Markov ================")
    sharedResources.markovHandler = MarkovHandler()
    print("============= YouTube ================")
    sharedResources.youtube = YouTubeData()
    print("=====================================")
    sharedResources.anilist = Anilist()

    # twitch bot acts as a master bot that appends other bot event loops to its own
    sharedResources.twitch_bot = run_twitch_bot(sharedResources)

    # bsky bot for posting / deleting go live notifications
    bsky_handle = getenv("BSKY_HANDLE")
    bsky_pw = getenv("BSKY_PW")
    if bsky_handle and bsky_pw:
        sharedResources.bsky_streamer = run_bsky_bot(bsky_handle, bsky_pw)

    # bsky bot for posting markov strings
    bsky_bot_handle = getenv("BSKY_BOT_HANDLE")
    bsky_bot_pw = getenv("BSKY_BOT_PW")
    if bsky_bot_handle and bsky_bot_pw:
        run_bsky_bot_markov(bsky_bot_handle, bsky_bot_pw, sharedResources.twitch_bot.loop, sharedResources.markovHandler)

    # verify and run discord bot
    # TODO: better verification, but empty is probably good enough
    discord_token = getenv('DISCORD_TOKEN')
    if discord_token and len(discord_token) > 0:
        sharedResources.discord_bot = run_discord_bot(sharedResources.twitch_bot.loop, sharedResources)

    # load the GUI window
    if getenv_int('ENABLE_GUI', 1):
        run_GUI(sharedResources.twitch_bot.loop, sharedResources)

    sharedResources.twitch_bot.run()

if __name__ == "__main__":
    run()
