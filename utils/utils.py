import os
import random
import re
from twitchio import Channel
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
    return f"User Not Found {username}"

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
async def replace_vars(message: str, ctx: commands.Context, channel: Channel) -> str:
    out_str = message

    # replace with a copy-paste of user's message
    if "$msg" in out_str:
        if ' ' in ctx.message.content:
            out_str = out_str.replace("$msg", ctx.message.content[ctx.message.content.index(' '):])
        else:
            out_str = out_str.replace("$msg", "")

    # replace with a mention of the user that posted the command
    if "$user" in out_str: out_str = out_str.replace("$user", ctx.message.author.mention)

    # this is currently broken in twitchio. fetch_followers returns what should be a paged list,
    # but instead returns the same list of followers every time.
    # if "$followcnt" in out_str:
    #     follow_count = 0
    #     streamer = await channel.user()
    #     followers = await streamer.fetch_followers(os.environ['CHANNEL_TOKEN'])
    #     while len(followers) > 0:
    #         follow_count += len(followers)
    #         followers = await streamer.fetch_followers(os.environ['CHANNEL_TOKEN'])
    #     out_str = out_str.replace("$followcnt", str(follow_count))

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

    # generate a random number in a range
    if "$randnum" in out_str:
        regex = r"\W*((?i)\$randnum\((?-i:))\W*([0-9]*),([0-9]*)\)"
        matches = re.match(regex, out_str)
        if matches is not None:
            match_groups = matches.groups()
            minimum = tryParseInt(match_groups[1], 0)
            maximum = tryParseInt(match_groups[2], 100)
            rand = random.randrange(minimum, maximum)
            
            out_str = f"{out_str[:matches.start()]}{rand}{out_str[matches.end():]}"
        else:
            out_str = out_str.replace("$randnum", "[$randnum must have a minimum and maximum: example \"$randnum(10,50)\"]")

    return out_str
