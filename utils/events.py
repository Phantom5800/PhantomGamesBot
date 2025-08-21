import inspect
from enum import Enum

class TwitchEventType(Enum):
    GoLive = 1
    EndStream = 2

class TwitchEvent:
    def __init__(self):
        self.twitch_event_log_listeners = []
        self.twitch_event_stream_event_listeners = []

    def register_events(self, obj):
        event_log_method = getattr(obj, "on_twitch_event_log")
        if event_log_method:
            self.twitch_event_log_listeners.append(event_log_method)

        stream_event_method = getattr(obj, "on_twitch_stream_event")
        if stream_event_method:
            self.twitch_event_stream_event_listeners.append(stream_event_method)

    async def twitch_log(self, msg):
        for func in self.twitch_event_log_listeners:
            await func(msg)

    async def twitch_stream_event(self, eventType: TwitchEventType, msg:str = None):
        for func in self.twitch_event_stream_event_listeners:
            await func(eventType, msg)

twitchevents = TwitchEvent()
