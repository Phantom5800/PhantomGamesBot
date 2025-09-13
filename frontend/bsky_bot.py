from atproto import Client, client_utils
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
            text_builder = client_utils.TextBuilder()
            text_builder.text(f"{msg} ")
            uri = f"https://twitch.tv/{user.lower()}"
            text_builder.link(uri, uri)
            self.live_post = self.client.send_post(text_builder)
        elif eventType == utils.events.TwitchEventType.EndStream and self.live_post:
            self.client.delete_post(self.live_post.uri)
            self.live_post = None

def run_bsky_bot(handle:str, password:str):
    bot = PhantomGamesBot(handle, password)
    return bot
