import os
from twitchio.ext import commands

debugPrintEnabled = False

def debugPrint(value: str):
    if debugPrintEnabled:
        print(value)

def tryParseInt(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

async def get_game_name_from_twitch(twitchClient: commands.Bot):
    streamer_list = await twitchClient.search_channels(os.environ['CHANNEL'])
    for streamer in streamer_list:
        debugPrint(f"[Get Game Name] Found streamer match: {streamer.name.lower()}")
        if streamer.name.lower() == os.environ['CHANNEL'].lower():
            game_ids = [streamer.game_id]
            debugPrint(f"[Get Game Name] Searching with game id: {streamer.game_id}")
            game_list = await twitchClient.fetch_games(game_ids)
            if len(game_list) > 0:
                game = game_list[0]
                debugPrint(f"[Get Game Name] Found game: {game.name}")
                return game.name
    return "No Category Set"

def convert_twitch_to_src_game(twitchGame: str) -> str:
    mapping = {
        "Pokémon: Let's Go, Eevee!": "Pokémon Let's Go Pikachu/Eevee",
        "Pokémon: Let's Go, Pikachu!": "Pokémon Let's Go Pikachu/Eevee"
    }
    if twitchGame in mapping:
        return mapping[twitchGame]
    return twitchGame

def replace_vars(message: str, ctx: commands.Context) -> str:
    out_str = message

    out_str = out_str.replace("$user", ctx.message.author.mention)

    return out_str
