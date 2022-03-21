import json
import threading
from copy import deepcopy
from datetime import datetime
import locale
import random

class QuoteHandler:
    def __init__(self):
        self.file_lock = threading.RLock()
        self.access_lock = threading.RLock()
    
    def load_quotes(self):
        self.file_lock.acquire()
        with open('./commands/resources/quotes.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.quotes = deepcopy(data)
                print(f"Quotes: {self.quotes}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load quotes from JSON")
                return
        self.file_lock.release()

    def save_quotes(self):
        self.file_lock.acquire()
        with open('./commands/resources/quotes.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.quotes)
            json_file.write(json_str)
        self.file_lock.release()

    def add_quote(self, quote: str, game: str) -> str:
        new_id = len(list(self.quotes.values()))
        date = datetime.now().strftime("%m/%d/%Y")
        quote_str = f"{quote} [{game}] [{date}]"
        self.access_lock.acquire()
        self.quotes[str(new_id)] = quote_str
        self.access_lock.release()
        self.save_quotes()
        return f"Added [Quote #{new_id}] -> {quote_str}"

    def edit_quote(self, quote_id: int, quote: str) -> str:
        self.access_lock.acquire()
        self.quotes[str(quote_id)] = quote
        self.access_lock.release()
        self.save_quotes()
        return f"Edited [Quote #{new_id}] -> {quote_str}"

    def remove_quote(self, quote_id: int) -> str:
        if quote_id < len(self.quotes):
            self.access_lock.acquire()
            for key in self.quotes.keys():
                intkey = int(key)
                if intkey == len(self.quotes.keys()) - 1:
                    del self.quotes[str(intkey)]
                    break
                elif intkey >= quote_id:
                    self.quotes[str(intkey)] = self.quotes[str(intkey + 1)]
            self.access_lock.release()
            self.save_quotes()
            return f"Removed [Quote #{quote_id}], all quotes after are shifted down"
        else:
            return f"[Quote #{quote_id}] does not exist"

    def find_quote_keyword(self, keywrd: str) -> str:
        self.access_lock.acquire()
        quotes = []
        for quote_id in self.quotes:
            if keywrd in self.quotes[quote_id]:
                quotes.append(f"[Quote #{quote_id}]: {self.quotes[quote_id]}")
        self.access_lock.release()
        if len(quotes) > 0:
            random_quote_id = random.randrange(len(quotes))
            return quotes[random_quote_id]
        return None

    def pick_specific_quote(self, quote_id: str) -> str:
        response = None
        self.access_lock.acquire()
        if quote_id in self.quotes:
            response = f"[Quote #{quote_id}]: {self.quotes[quote_id]}"
        self.access_lock.release()
        return response

    def pick_random_quote(self) -> str:
        self.access_lock.acquire()
        quote_id = random.randrange(len(list(self.quotes.values())))
        quote = self.quotes[str(quote_id)]
        self.access_lock.release()
        return f"[Quote #{quote_id}]: {quote}"
