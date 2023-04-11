import googleapiclient.discovery
import json
import os
import threading
from copy import deepcopy

class YouTubeData:
    def __init__(self):
        self.access_lock = threading.RLock()
        self.youtube_data = {}

        self.load_youtube_config()
        self.setup_youtube_api()

    def setup_youtube_api(self):
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ.get('YOUTUBE_API_KEY'))

    def load_youtube_config(self):
        self.access_lock.acquire()
        root = './commands/resources/channels/'
        for folder in os.listdir(root):
            channel_folder = os.path.join(root, folder)
            if os.path.isdir(channel_folder):
                youtube_file = os.path.join(channel_folder, "youtube_data.json")
                if os.path.isfile(youtube_file):
                    with open(youtube_file, 'r', encoding="utf-8") as json_file:
                        try:
                            data = json.load(json_file)
                            self.youtube_data[folder] = deepcopy(data)
                        except json.decoder.JSONDecodeError:
                            print(f"[ERROR] Failed to load YouTube config from JSON for {folder}")
        self.access_lock.release()
    
    '''
    Get the sub count of whatever youtube account is bound to the given twitch channel.
    '''
    def get_subscriber_count(self, channel: str) -> int:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("username"):
            request = self.youtube.channels().list(
                part="statistics",
                forUsername=self.youtube_data[channel]["username"]
            )
            response = request.execute()
            for channel in response.get("items"):
                if channel.get("statistics"):
                    if channel["statistics"].get("subscriberCount"):
                        return int(channel["statistics"]["subscriberCount"])
        return 0

    '''
    Generate a message to be returned for channel specific youtube commands.
    '''
    def get_youtube_com_message(self, channel: str) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel):
            youtube_url = "https://youtube.com"
            if self.youtube_data[channel].get("handle"):
                youtube_url = f"{youtube_url}/@{self.youtube_data[channel].get('handle')}"
            else:
                youtube_url = f"{youtube_url}/channel/{self.youtube_data[channel].get('channel_id')}"

            subgoal = self.youtube_data[channel].get("subgoal")
            submsg =  self.youtube_data[channel].get("subgoal_message")
            if subgoal > 0:
                subcount = self.get_subscriber_count(channel)
                return f"We are currently at {subcount} / {subgoal} subscribers on YouTube! {submsg} {youtube_url}"
            else:
                return f"{submsg} {youtube_url}"
        
        return ""

    '''
    Get a link to the most recent video uploaded by a given channel.
    '''
    def get_most_recent_video(self, channel: str) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("channel_id"):
            # find most recent upload for channel
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.youtube_data[channel]["channel_id"],
                maxResults=1,
                order="date"
            )
            response = request.execute()
            base_url = "https://youtube.com/watch?v="
            videoId = ""
            for video in response.get("items"):
                if video.get("id"):
                    if video["id"].get("videoId"):
                        videoId = video["id"]["videoId"]
                        break
            if len(videoId) < 1:
                return ""
            
            # get video title
            request = self.youtube.videos().list(
                part="snippet",
                id=videoId
            )
            response = request.execute()
            title = ""
            for metadata in response.get("items"):
                if metadata.get("snippet"):
                    title = metadata["snippet"].get("title")

            return f"{title} - {base_url + videoId}"
        return ""
