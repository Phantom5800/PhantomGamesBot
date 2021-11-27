import random

class MemeResponse:
    def __init__(self, memeFilename):
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

    def add_response(self, response):
        self.responses.append(response)
        self.save_memes()

    def get_random_response(self):
        id = random.randrange(len(self.responses))
        return self.responses[id]
