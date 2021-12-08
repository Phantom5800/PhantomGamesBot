import asyncio
import os
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
from commands.src import SrcomApi
from frontend.twitch_bot import run_twitch_bot
from frontend.discord_bot import run_discord_bot

if __name__ == "__main__":
    # Shared resources
    customCommandHandler = CustomCommands()
    quoteHandler = QuoteHandler()
    print("========== Custom Commands ==========")
    customCommandHandler.load_commands()
    print("============== Quotes ===============")
    quoteHandler.load_quotes()
    print("=============== SRC =================")
    srcHandler = SrcomApi()
    print("=====================================")

    # twitch bot acts as a master bot that appends other bot event loops to its own
    masterBot = run_twitch_bot(customCommandHandler, quoteHandler, srcHandler)

    # verify and run discord bot
    # TODO: better verification, but empty is probably good enough
    if os.environ['DISCORD_TOKEN'] is not None and len(os.environ['DISCORD_TOKEN']) > 0:
        run_discord_bot(masterBot.loop, customCommandHandler, quoteHandler, srcHandler)

    masterBot.run()
