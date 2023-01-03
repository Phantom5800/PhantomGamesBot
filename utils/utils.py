import os
import random
import re
from twitchio import Channel
from twitchio.ext import commands as twitchCommands

debugPrintEnabled = False

def debugPrint(value: str):
    if debugPrintEnabled:
        print(value)

def tryParseInt(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

twitch_user_cache = {}

'''
Get a user object from cache if it exists, otherwise make a request and store the result.
'''
async def get_twitch_user(twitchClient: twitchCommands.Bot, username: str):
    if username in twitch_user_cache:
        return twitch_user_cache[username]
    streamer = await twitchClient.fetch_channel(username)
    if streamer is not None:
        twitch_user_cache[username] = streamer
    return streamer

'''
Find the current stream category for a given user.
'''
async def get_game_name_from_twitch_for_user(twitchClient: twitchCommands.Bot, username: str) -> str:
    # get the channel info for requested user, this should typically work immediately
    streamer = await get_twitch_user(twitchClient, username)
    if streamer is not None:
        debugPrint(f"[Get Game Name] Found streamer immediately: {username}")
        return streamer.game_name

    # backup, do a full search
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
    return f"User Not Found {username}"

'''
Get the stream title for a specific user.
'''
async def get_stream_title_for_user(twitchClient: twitchCommands.Bot, username: str) -> str:
    streamer = await get_twitch_user(twitchClient, username)
    if streamer is not None:
        return streamer.title
    return f"User Not Found {username}"

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
Generic variable replacement that does not depend on any platform specific features.
'''
async def replace_vars_generic(message: str) -> str:
    out_str = message

    # generate a random number in a range
    if "$randnum" in out_str:
        regex = r"(.*)\W*((?i)\$randnum\((?-i:))\W*([0-9]*),([0-9]*)\)(.*)"
        matches = re.match(regex, out_str)
        if matches is not None:
            match_groups = matches.groups()
            minimum = tryParseInt(match_groups[2], 0)
            maximum = tryParseInt(match_groups[3], 100)
            rand = random.randint(minimum, maximum)
            
            start = len(matches.groups()[0])
            end = len(matches.groups()[0]) + len(matches.groups()[1]) + len(matches.groups()[2]) + len(matches.groups()[3]) + 2
            out_str = f"{out_str[:start]}{rand}{out_str[end:]}"
        else:
            out_str = out_str.replace("$randnum", "[$randnum must have a minimum and maximum: example \"$randnum(10,50)\"]")
    
    return out_str

'''
Variable replacement for bot responses.
'''
async def replace_vars_twitch(message: str, ctx: twitchCommands.Context, channel: Channel) -> str:
    out_str = message

    # replace with a copy-paste of user's message
    if "$msg" in out_str:
        if ' ' in ctx.message.content:
            out_str = out_str.replace("$msg", ctx.message.content[ctx.message.content.index(' '):])
        else:
            out_str = out_str.replace("$msg", "")

    # replace with a mention of the user that posted the command
    if "$user" in out_str: out_str = out_str.replace("$user", ctx.message.author.mention)

    # mention a user from chat at random
    if "$randuser" in out_str:
        chat_users = list(channel.chatters)
        user_id = random.randrange(len(chat_users))
        out_str = out_str.replace("$randuser", chat_users[user_id].mention)

    # mention a random mod in chat
    if "$randmod" in out_str:
        chat_users = list(filter(lambda user: user.is_mod, list(channel.chatters)))
        user_id = random.randrange(len(chat_users))
        out_str = out_str.replace("$randmod", chat_users[user_id].mention)

    # mentions a random sub in chat
    if "$randsub" in out_str:
        chat_users = list(filter(lambda user: user.is_subscriber, list(channel.chatters)))
        user_id = random.randrange(len(chat_users))
        out_str = out_str.replace("$randmod", chat_users[user_id].mention)

    # handle generic variables last
    out_str = await replace_vars_generic(out_str)

    return out_str
