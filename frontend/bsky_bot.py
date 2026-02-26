from atproto import Client, client_utils, models
from datetime import datetime
import os
import random
import utils.events

class PhantomGamesBot:
    def __init__(self, handle:str, password:str, stream_notif_mode:bool, markov_mode:bool):
        self.live_post = None
        self.client = Client()
        self.valid_channels = ["phantom5800"]
        try:
            self.client.login(login=handle, password=password)
        except ValueError as e:
            print(f"[BSKY Error] {e}")
            return
        except:
            print(f"[BSKY Error] Invalid-Handle bullshit")
            return
        print(f"[BSKY] Logged in to {handle}")
        utils.events.twitchevents.register_events(self)

        self.stream_notif_mode = stream_notif_mode
        self.generated_message_mode = markov_mode

    async def get_img_data(self, game:str):
        # remove common bad path characters
        game = game.translate(str.maketrans('', '', '<>:\"/\\|?* '))
        base_path = f'./commands/resources/images/{game}'

        # if the game path exists, pick a random image file and return it
        if os.path.isdir(base_path):
            files = [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]
            random_idx = random.randrange(len(files))
            selected_image = os.path.join(base_path, files[random_idx])
            print(f"[BSKY] Go live with image: {selected_image}")
            with open(selected_image, 'rb') as f:
                return f.read()
        return None

    async def on_twitch_stream_event(self, user:str, eventType:utils.events.TwitchEventType, msg:str):
        if self.stream_notif_mode:
            username = user.lower()
            if username in self.valid_channels:
                if eventType == utils.events.TwitchEventType.GoLive:
                    text_builder = client_utils.TextBuilder()
                    text_builder.text(f"{msg} ")
                    uri = f"https://twitch.tv/{username}"
                    text_builder.link(uri, uri)

                    game = msg[:msg.index('|')].strip()
                    img = await self.get_img_data(game)
                    if img is not None:
                        aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=720, width=1280)
                        self.live_post = self.client.send_image(text=text_builder, image=img, image_alt=uri, image_aspect_ratio=aspect_ratio)
                    else:
                        self.live_post = self.client.send_post(text=text_builder)
                elif eventType == utils.events.TwitchEventType.EndStream and self.live_post:
                    self.client.delete_post(self.live_post.uri)
                    self.live_post = None

    async def on_generate_post(self, msg:str):
        if self.generated_message_mode:
            text_builder = client_utils.TextBuilder()
            text_builder.text(msg)
            self.client.send_post(text=text_builder)
            print(f"[{datetime.now()}] Generated Bsky Post: {msg}")

def run_bsky_bot(handle:str, password:str, stream_notif_mode:bool = False, markov_mode:bool = False):
    bot = PhantomGamesBot(handle, password, stream_notif_mode, markov_mode)
    return bot
