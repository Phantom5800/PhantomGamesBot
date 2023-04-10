import random
from enum import Enum

class SlotsMode(Enum):
    TWITCH=1
    DISCORD=2

class Slots:
    def __init__(self, mode: SlotsMode):
        if mode == SlotsMode.TWITCH:
            self.emotes = [
                "phanto274GG",
                "phanto274Bless",
                "phanto274Shrug",
                "phanto274Smile",
                "D:",
                "Boris",
                "COPIUM",
                "Ezekiel",
                "Flushed",
                "SoniaKnows",
                "weedMario",
                "WhatsHisFace",
                "yoshiGasm",
                "MarioDab",
                "el:Wadafa:yelpanaFrienddandoleunabrazo",
                "GoombarioLookingOutHisJailCell"
            ]
        elif mode == SlotsMode.DISCORD:
            self.emotes = [
                "<:phanto274Awoo:935285686536376351>",
                "<:phanto274Bless:949504367004901386>",
                "<:phanto274Shrug:948047831325872178>",
                "<:phanto274Smile:948047802523598878>",
                "<:phanto274Snake:844628263951138886>",
                "<:Boris:945583854830387211>",
                "<:Ezekiel3:1000994189460389888>",
                "<:phanto274Pog:844628236961054751>",
                "<:mvBirthday:1000994191679172628>",
                "<:MarioDab:1000994190563483718>",
                "<:16Percent:945584341227024425>",
            ]
    
    def roll(self, user):
        result = f"{user} {self.emotes[random.randint(0, len(self.emotes)-1)]} | {self.emotes[random.randint(0, len(self.emotes)-1)]} | {self.emotes[random.randint(0, len(self.emotes)-1)]}"
        return result
