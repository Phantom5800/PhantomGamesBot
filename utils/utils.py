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

'''
Find the current stream category for a given user.
'''
async def get_game_name_from_twitch_for_user(twitchClient: commands.Bot, username: str) -> str:
    streamer_list = await twitchClient.search_channels(username)
    for streamer in streamer_list:
        debugPrint(f"[Get Game Name] Found streamer match: {streamer.name.lower()}")
        if streamer.name.lower() == username.lower():
            game_ids = [streamer.game_id]
            debugPrint(f"[Get Game Name] Searching with game id: {streamer.game_id}")
            game_list = await twitchClient.fetch_games(game_ids)
            if len(game_list) > 0:
                game = game_list[0]
                debugPrint(f"[Get Game Name] Found game: {game.name}")
                return game.name
            return "No Category Set"
    return "User Not Found"

'''
Find the current game being played on the streamer's channel.
'''
async def get_game_name_from_twitch(twitchClient: commands.Bot) -> str:
    game = await get_game_name_from_twitch_for_user(twitchClient, os.environ['CHANNEL'])
    return game

'''
Take game name's from twitch and map them to the name of games that appear on speedrun.com.
'''
def convert_twitch_to_src_game(twitchGame: str) -> str:
    mapping = {
        "Pokémon: Let's Go, Eevee!": "Pokémon Let's Go Pikachu/Eevee",
        "Pokémon: Let's Go, Pikachu!": "Pokémon Let's Go Pikachu/Eevee"
    }
    if twitchGame in mapping:
        return mapping[twitchGame]
    return twitchGame

'''
Variable replacement for bot responses.
'''
def replace_vars(message: str, ctx: commands.Context) -> str:
    out_str = message

    if "$user" in out_str: out_str = out_str.replace("$user", ctx.message.author.mention)
    if "$msg" in out_str: out_str = out_str.replace("$msg", ctx.message.content[ctx.message.content.index(' '):])

    return out_str
