import googleapiclient.discovery
import json
import os
import threading
from copy import deepcopy
from datetime import datetime, timedelta

class YouTubeData:
    def __init__(self):
        self.access_lock = threading.RLock()
        self.youtube_data = {}

        self.load_youtube_config()
        self.setup_youtube_api()

        self.cache = {}

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

    def save_youtube_config(self, channel: str):
        channel = channel.lower()
        self.access_lock.acquire()
        with open(f'./commands/resources/channels/{channel}/youtube_data.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.youtube_data[channel], indent=2)
            json_file.write(json_str)
        self.access_lock.release()
    
    def get_cache(self, channel: str, cache_field: str):
        if not self.cache.get(channel):
            self.cache[channel] = {}
        if not self.cache[channel].get(cache_field):
            self.cache[channel][cache_field] = {
                "data": None,
                "set_time": timestamp.now()
            }
        return self.cache[channel][cache_field]

    def set_cache(self, channel: str, cache_field: str, data):
        if not self.cache.get(channel):
            self.cache[channel] = {}
        self.cache[channel][cache_field] = {
            "data": data,
            "set_time": timestamp.now()
        }

    '''
    Get the sub count of whatever youtube account is bound to the given twitch channel.

    Note: YouTube API Quota cost = 1
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
            elif self.youtube_data[channel].get('channel_id'):
                youtube_url = f"{youtube_url}/channel/{self.youtube_data[channel].get('channel_id')}"
            else:
                return "" # exit immediately if no youtube channel is configured

            subgoal = self.youtube_data[channel].get("subgoal")
            submsg =  self.youtube_data[channel].get("subgoal_message")
            if subgoal > 0:
                subcount = self.get_subscriber_count(channel)
                return f"We are currently at {subcount} / {subgoal} subscribers on YouTube! {submsg} {youtube_url}"
            return f"{submsg} {youtube_url}"
        
        return ""

    '''
    Get a link to the most recent video uploaded by a given channel.

    Note: YouTube API Quota cost = 101 (100 for search, 1 for videos)
    '''
    def get_most_recent_video(self, channel: str) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("channel_id"):
            # refresh youtube api
            self.setup_youtube_api()

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
    
    '''
    Get number of videos and total length matching a query

    Note: This call is very expensive for the YouTube API quota and needs to be cached.
          Estimated quota cost is 101 for every 50 videos that query hits.
    '''
    def get_total_video_length(self, channel: str, query: str = "") -> tuple:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("channel_id"):
            # refresh youtube api
            self.setup_youtube_api()

            request = self.youtube.search().list(
                part="snippet",
                channelId=self.youtube_data[channel]["channel_id"],
                order="date",
                maxResults=50,
                q=query
            )
            response = request.execute()

            total_duration = timedelta()
            total_videos = response["pageInfo"].get("totalResults")
            while True:
                video_id_list = ""
                first = True
                for video in response.get("items"):
                    if first:
                        first = False
                    else:
                        video_id_list += ","
                    
                    if video.get("id"):
                        if video["id"].get("videoId"):
                            video_id_list += str(video["id"]["videoId"])

                video_request = self.youtube.videos().list(
                    part="snippet,contentDetails",
                    id=video_id_list
                )
                video_data = video_request.execute()

                def get_isosplit(s, split):
                    if split in s:
                        n, s = s.split(split)
                    else:
                        n = 0
                    return n, s

                def parse_isoduration(s):
                    # Remove prefix
                    s = s.split('P')[-1]
                    
                    # Step through letter dividers
                    days, s = get_isosplit(s, 'D')
                    _, s = get_isosplit(s, 'T')
                    hours, s = get_isosplit(s, 'H')
                    minutes, s = get_isosplit(s, 'M')
                    seconds, s = get_isosplit(s, 'S')

                    # Convert all to seconds
                    return timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds))

                for video in video_data.get("items"):
                    print(video.get("snippet").get("title"))
                    if video.get("contentDetails"):
                        duration = video["contentDetails"].get("duration")
                        if duration:
                            total_duration += parse_isoduration(duration)

                if not response.get("nextPageToken"):
                    break
                request = self.youtube.search().list(
                    part="snippet",
                    channelId=self.youtube_data[channel]["channel_id"],
                    order="date",
                    maxResults=50,
                    q=query,
                    pageToken=response["nextPageToken"]
                )
                response = request.execute()

            return total_videos, total_duration

        return 0, timedelta()

    '''
    Set the YouTube channel data associated with the twitch user.
    '''
    def set_youtube_channel_data(self, channel: str, username: str, channelId: str):
        channel = channel.lower()
        self.youtube_data[channel]["username"] = username
        self.youtube_data[channel]["channel_id"] = channelId
        self.save_youtube_config(channel)

    '''
    Set the YouTube Handle paramater.
    '''
    def set_youtube_handle(self, channel: str, handle: str):
        channel = channel.lower()
        self.youtube_data[channel]["handle"] = handle
        self.save_youtube_config(channel)

    '''
    Set the channel sub goal and message.
    '''
    def set_youtube_subgoal(self, channel: str, goal: int, message: str):
        channel = channel.lower()
        self.youtube_data[channel]["subgoal"] = goal
        self.youtube_data[channel]["subgoal_message"] = message
        self.save_youtube_config(channel)
    