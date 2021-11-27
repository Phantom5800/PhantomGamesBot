import random
from twitchio.ext import commands

class MemeResponse:
    def __init__(self, memeFilename: str):
        self.responses = []
        self.memeFile = f"./commands/resources/{memeFilename}.txt"
        with open(self.memeFile, 'r', encoding="utf-8") as txt_file:
            lines = txt_file.readlines()
            for line in lines:
                response = line.strip()
                self.responses.append(response)
    
    def save_memes(self):
        with open(self.memeFile, 'w', encoding="utf-8") as txt_file:
            for meme in self.responses:
                txt_file.write(f"{meme}\n")

    def add_response(self, response: str):
        self.responses.append(response)
        self.save_memes()

    def get_seeded_response(self, seed: int) -> str:
        if len(self.responses) > 0:
            id = seed % len(self.responses)
            return self.responses[id]
        return None

    def get_random_response(self) -> str:
        if len(self.responses) > 0:
            id = random.randrange(len(self.responses))
            return self.responses[id]
        return None
