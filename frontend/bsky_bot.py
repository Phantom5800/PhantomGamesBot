from atproto import Client
import utils.events

class PhantomGamesBot:
    def __init__(self, handle:str, password:str):
        self.live_post = None
        self.client = Client()
        try:
            self.client.login(login=handle, password=password)
        except ValueError as e:
            print(f"[BSKY Error] {e}")
        utils.events.twitchevents.register_events(self)

    async def on_twitch_stream_event(self, user:str, eventType:utils.events.TwitchEventType, msg:str):
        if eventType == utils.events.TwitchEventType.GoLive:
            print(f"[BSKY Live] {msg}")
        elif eventType == utils.events.TwitchEventType.EndStream:
            print(f"[BSKY End] {msg}")

def run_bsky_bot(handle:str, password:str):
    bot = PhantomGamesBot(handle, password)
    return bot
