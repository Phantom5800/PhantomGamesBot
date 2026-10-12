# standard libraries
import random

# twitch
from twitchio import Channel
from twitchio.ext import commands as twitchCommands

# PhantomGamesBot
from .utils import debugPrint, replace_vars_generic

twitch_user_cache = {}

async def get_twitch_user(twitchClient: twitchCommands.Bot, username: str, reset_cache: bool = False):
    '''Get a user object from cache if it exists, otherwise make a request and store the result.'''
    if reset_cache == False and username in twitch_user_cache:
        return twitch_user_cache[username]
    streamer = await twitchClient.fetch_channel(username)
    if streamer is not None:
        twitch_user_cache[username] = streamer
    return streamer

async def get_game_name_from_twitch_for_user(twitchClient: twitchCommands.Bot, username: str) -> str:
    '''Find the current stream category for a given user.'''
    # get the channel info for requested user, this should typically work immediately
    streamer = await get_twitch_user(twitchClient, username, reset_cache=True)
    if streamer is not None:
        debugPrint(f"[Get Game Name] Found streamer immediately: {username} playing {streamer.game_name}: {streamer.game_id}")
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
                debugPrint(f"[Get Game Name] Found game: {game.name}: {streamer.game_id}")
                return game.name
            return "No Category Set"
    return f"User Not Found {username}"

async def get_stream_title_for_user(twitchClient: twitchCommands.Bot, username: str) -> str:
    '''Get the stream title for a specific user.'''
    streamer = await get_twitch_user(twitchClient, username, reset_cache=True)
    if streamer is not None:
        return streamer.title
    return f"User Not Found {username}"

async def replace_vars_twitch(message: str, ctx: twitchCommands.Context, channel: Channel) -> str:
    '''Variable replacement for bot responses.'''
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
