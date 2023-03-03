import json
import os
import threading
from copy import deepcopy
from datetime import datetime
import locale
import random

class QuoteHandler:
    def __init__(self):
        self.file_lock = threading.RLock()
        self.access_lock = threading.RLock()
        self.quotes = {}
    
    def load_quotes(self):
        self.file_lock.acquire()
        root = './commands/resources/channels/'
        for folder in os.listdir(root):
            channel_folder = os.path.join(root, folder)
            if os.path.isdir(channel_folder):
                quotes_file = os.path.join(channel_folder, "quotes.json")
                if os.path.isfile(quotes_file):
                    with open(quotes_file, 'r', encoding="utf-8") as json_file:
                        try:
                            data = json.load(json_file)
                            self.quotes[folder] = deepcopy(data)
                            print(f"Quotes [{folder}]: {len(self.quotes[folder])}")
                        except json.decoder.JSONDecodeError:
                            print(f"[ERROR] Failed to load quotes from JSON for {folder}")
                            continue
        self.file_lock.release()

    def save_quotes(self, channel: str):
        channel = channel.lower()
        self.file_lock.acquire()
        with open(f'./commands/resources/channels/{channel}/quotes.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.quotes[channel], indent=2)
            json_file.write(json_str)
        self.file_lock.release()

    def add_quote(self, quote: str, game: str, channel: str) -> str:
        channel = channel.lower()
        new_id = len(list(self.quotes[channel].values()))
        date = datetime.now().strftime("%m/%d/%Y")
        quote_str = f"{quote} [{game}] [{date}]"
        self.access_lock.acquire()
        self.quotes[channel][str(new_id)] = quote_str
        self.access_lock.release()
        self.save_quotes(channel)
        return f"Added [Quote #{new_id}] -> {quote_str}"

    def edit_quote(self, quote_id: int, quote: str, channel: str) -> str:
        channel = channel.lower()
        self.access_lock.acquire()
        self.quotes[channel][str(quote_id)] = quote
        self.access_lock.release()
        self.save_quotes(channel)
        return f"Edited [Quote #{new_id}] -> {quote_str}"

    def remove_quote(self, quote_id: int, channel: str) -> str:
        channel = channel.lower()
        if quote_id < len(self.quotes[channel]):
            self.access_lock.acquire()
            for key in self.quotes[channel].keys():
                intkey = int(key)
                if intkey == len(self.quotes[channel].keys()) - 1:
                    del self.quotes[channel][str(intkey)]
                    break
                elif intkey >= quote_id:
                    self.quotes[channel][str(intkey)] = self.quotes[channel][str(intkey + 1)]
            self.access_lock.release()
            self.save_quotes(channel)
            return f"Removed [Quote #{quote_id}], all quotes after are shifted down"
        else:
            return f"[Quote #{quote_id}] does not exist"

    def find_quote_keyword(self, keywrd: str, channel: str) -> str:
        channel = channel.lower()
        self.access_lock.acquire()
        quotes = []
        for quote_id in self.quotes[channel]:
            if keywrd.lower() in self.quotes[channel][quote_id].lower():
                quotes.append(f"[Quote #{quote_id}]: {self.quotes[channel][quote_id]}")
        self.access_lock.release()
        if len(quotes) > 0:
            random_quote_id = random.randrange(len(quotes))
            return quotes[random_quote_id]
        return None

    def pick_specific_quote(self, quote_id: str, channel: str) -> str:
        channel = channel.lower()
        response = "Could not find a quote"
        self.access_lock.acquire()
        if quote_id in self.quotes[channel]:
            response = f"[Quote #{quote_id}]: {self.quotes[channel][quote_id]}"
        self.access_lock.release()
        return response

    def pick_random_quote(self, channel: str) -> str:
        channel = channel.lower()
        self.access_lock.acquire()
        quote_id = random.randrange(len(list(self.quotes[channel].values())))
        quote = self.quotes[channel][str(quote_id)]
        self.access_lock.release()
        return f"[Quote #{quote_id}]: {quote}"

    def num_quotes(self, channel: str) -> int:
        return len(self.quotes[channel.lower()])
