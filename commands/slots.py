import random

class Slots:
    def __init__(self):
        self.emotes = [
            "phanto274Awoo",
            "phanto274Bless",
            "phanto274Shrug",
            "phanto274Smile",
            "COPIUM",
            "D:",
            "Flushed",
            "weedMario",
            "Boris"
        ]
    
    def roll(self, user):
        result = ""
        result = f"{user} {self.emotes[random.randint(0, len(self.emotes))]} | {self.emotes[random.randint(0, len(self.emotes))]} | {self.emotes[random.randint(0, len(self.emotes))]}"
        return result
