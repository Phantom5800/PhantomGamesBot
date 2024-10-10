import inspect

class TwitchEvent:
    def __init__(self):
        self.twitch_event_log_listeners = []

    def register_events(self, obj):
        method = getattr(obj, "on_twitch_event_log")
        self.twitch_event_log_listeners.append(method)

    async def twitch_log(self, msg):
        for func in self.twitch_event_log_listeners:
            await func(msg)

twitchevents = TwitchEvent()
