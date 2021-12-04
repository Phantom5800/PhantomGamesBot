import asyncio
from commands.custom_commands import CustomCommands
from commands.quotes import QuoteHandler
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
    print("=====================================")

    # TODO: verify twitch environment before running bot
    masterBot = run_twitch_bot(customCommandHandler, quoteHandler)

    # TODO: add discord frontend
    run_discord_bot(masterBot.loop, customCommandHandler, quoteHandler)

    masterBot.run()
