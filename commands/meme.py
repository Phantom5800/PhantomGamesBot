import random
import threading
from twitchio.ext import commands

class MemeResponse:
    def __init__(self, memeFilename: str):
        self.access_lock = threading.RLock()
        self.responses = []
        self.memeFile = f"./commands/resources/{memeFilename}.txt"
        with open(self.memeFile, 'r', encoding="utf-8") as txt_file:
            lines = txt_file.readlines()
            for line in lines:
                response = line.strip()
                self.responses.append(response)
    
    def save_memes(self):
        self.access_lock.acquire()
        with open(self.memeFile, 'w', encoding="utf-8") as txt_file:
            for meme in self.responses:
                txt_file.write(f"{meme}\n")
        self.access_lock.release()

    def add_response(self, response: str):
        self.access_lock.acquire()
        self.responses.append(response)
        self.save_memes()
        self.access_lock.release()

    def get_seeded_response(self, seed: int) -> str:
        response = None
        self.access_lock.acquire()
        if len(self.responses) > 0:
            id = seed % len(self.responses)
            response = self.responses[id]
        self.access_lock.release()
        return response

    def get_random_response(self) -> str:
        response = None
        self.access_lock.acquire()
        if len(self.responses) > 0:
            id = random.randrange(len(self.responses))
            response = self.responses[id]
        self.access_lock.release()
        return response
