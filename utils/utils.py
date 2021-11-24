import os

def tryParseInt(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

async def getGameNameFromClient(client):
    streamer_list = await client.search_channels(os.environ['CHANNEL'])
    for streamer in streamer_list:
        if streamer.name.lower() == os.environ['CHANNEL'].lower():
            game_ids = [streamer.game_id]
            game_list = await client.fetch_games(game_ids)
            if len(game_list) > 0:
                game = game_list[0]
                return game.name
    return "No Category Set"

