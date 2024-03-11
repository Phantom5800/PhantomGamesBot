import googleapiclient.discovery
import json
import os
import threading
import traceback
from copy import deepcopy
from datetime import datetime, timedelta

class YouTubeData:
    def __init__(self):
        self.access_lock = threading.RLock()
        self.youtube_data = {}

        self.load_youtube_config()
        self.setup_youtube_api()

        self.cache = {}
        try:
            for channel in self.youtube_data:
                self.cache_youtube_data(channel)
        except:
            tb = traceback.format_exc()
            print(f"--------\n\t{tb}\n--------")
        else:
            print("YouTube data has been initialized")

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

    def cache_youtube_data(self, channel: str):
        channel = channel.lower()
        if self.youtube_data[channel].get("playlists"):
            self.cache[channel] = {}
            for playlist in self.youtube_data[channel]["playlists"]:
                try:
                    self.cache[channel][playlist] = self.get_total_video_length(channel, self.youtube_data[channel]["playlists"][playlist])
                except:
                    raise
    
    def get_cache_youtube_playlist_length(self, channel: str, playlist: str) -> tuple:
        channel = channel.lower()
        if self.cache.get(channel):
            if self.cache[channel].get(playlist):
                return self.cache[channel][playlist]
        return 0,None

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

    def get_youtube_url(self, channel: str) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel):
            youtube_url = "https://youtube.com"
            if self.youtube_data[channel].get("handle"):
                youtube_url = f"{youtube_url}/@{self.youtube_data[channel].get('handle')}"
            elif self.youtube_data[channel].get('channel_id'):
                youtube_url = f"{youtube_url}/channel/{self.youtube_data[channel].get('channel_id')}"
            else:
                return ""
            return youtube_url
        return ""

    '''
    Generate a message to be returned for channel specific youtube commands.
    '''
    def get_youtube_com_message(self, channel: str) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel):
            youtube_url = self.get_youtube_url(channel)
            if len(youtube_url) == 0:
                return "" # exit immediately if no url

            subgoal = self.youtube_data[channel].get("subgoal")
            submsg =  self.youtube_data[channel].get("subgoal_message")
            genericmsg = self.youtube_data[channel].get("generic_msg")
            if subgoal > 0:
                subcount = self.get_subscriber_count(channel)
                if subcount >= subgoal:
                    return f"We hit our YouTube sub goal to {submsg} and will be starting that soon! {genericmsg} {youtube_url}"
                return f"We are currently at {subcount} / {subgoal} subscribers on YouTube! When we hit that goal we will {submsg}! {genericmsg} {youtube_url}"
            return f"{genericmsg} {youtube_url}"
        
        return ""

    '''
    Get a link to the most recent video uploaded by a given channel.

    Note: YouTube API Quota cost = 101 (100 for search, 1 for videos). Only 2 if use_playlist_api is True!
    '''
    def get_most_recent_video(self, channel: str, use_playlist_api: bool = False) -> str:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("channel_id"):
            # refresh youtube api
            self.setup_youtube_api()

            # find most recent upload for channel
            request = None

            # use the uploads playlist for a channel to get latest video
            if use_playlist_api:
                playlist_id = self.youtube_data[channel]["channel_id"]
                playlist_id = playlist_id[0:1] + "U" + playlist_id[2:]
                request = self.youtube.playlistItems().list(
                    part="snippet,status",
                    maxResults=1,
                    playlistId=playlist_id
                )
            else:
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
                if video.get("snippet"):
                    if video["snippet"].get("resourceId"):
                        if video["snippet"]["resourceId"].get("videoId"):
                            videoId = str(video["snippet"]["resourceId"]["videoId"])
                            break

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

    Note: This should get cached since the data doesn't change very often.
          Estimated quota cost is 2 for every 50 videos that query hits.
    '''
    def get_total_video_length(self, channel: str, playlist_id: str = "") -> tuple:
        channel = channel.lower()
        if self.youtube_data.get(channel) and self.youtube_data[channel].get("channel_id"):
            # refresh youtube api
            self.setup_youtube_api()

            request = self.youtube.playlistItems().list(
                part="snippet,status",
                maxResults=50,
                playlistId=playlist_id
            )
            response = None
            try:
                response = request.execute()
            except Exception as e:
                print(f"[YouTube Error] Error getting playlist: {playlist_id} - {e}")
                raise

            total_duration = timedelta()
            total_videos = 0
            while True:
                video_id_list = ""
                first = True
                for video in response.get("items"):
                    # skip over private videos in a playlist
                    if video.get("status"):
                        if video["status"].get("privacyStatus") == "private":
                            continue

                    if first:
                        first = False
                    else:
                        video_id_list += ","
                    
                    if video.get("snippet"):
                        if video["snippet"].get("resourceId"):
                            if video["snippet"]["resourceId"].get("videoId"):
                                total_videos += 1
                                video_id_list += str(video["snippet"]["resourceId"]["videoId"])

                video_request = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics",
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
                    if video.get("contentDetails"):
                        duration = video["contentDetails"].get("duration")
                        if duration:
                            total_duration += parse_isoduration(duration)
                    if video.get("statistics"):
                        views = video["statistics"].get("viewCount")

                if not response.get("nextPageToken"):
                    break
                request = self.youtube.playlistItems().list(
                    part="snippet,status",
                    maxResults=50,
                    playlistId=playlist_id,
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
    