import json
from copy import deepcopy
from datetime import datetime
import locale
import random

class QuoteHandler:
    def load_quotes(self):
        with open('./commands/resources/quotes.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.quotes = deepcopy(data)
                print(f"Quotes: {self.quotes}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load quotes from JSON")
                return

    def save_quotes(self):
        with open('./commands/resources/quotes.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.quotes)
            json_file.write(json_str)

    def add_quote(self, quote: str, game: str) -> str:
        new_id = len(list(self.quotes.values()))
        date = datetime.now().strftime("%m/%d/%Y")
        quote_str = f"{quote} [{game}] [{date}]"
        self.quotes[str(new_id)] = quote_str
        self.save_quotes()
        return f"Added [Quote #{new_id}] -> {quote_str}"

    def edit_quote(self, quote_id: int, quote: str) -> str:
        self.quotes[str(quote_id)] = quote
        self.save_quotes()
        return f"Edited [Quote #{new_id}] -> {quote_str}"

    def remove_quote(self, quote_id: int) -> str:
        if quote_id < len(self.quotes):
            for key in self.quotes.keys():
                intkey = int(key)
                if intkey == len(self.quotes.keys()) - 1:
                    del self.quotes[str(intkey)]
                    break
                elif intkey >= quote_id:
                    self.quotes[str(intkey)] = self.quotes[str(intkey + 1)]
            self.save_quotes()
            return f"Removed [Quote #{quote_id}], all quotes after are shifted down"
        else:
            return f"[Quote #{quote_id}] does not exist"

    def pick_specific_quote(self, quote_id: str) -> str:
        if quote_id in self.quotes:
            return f"[Quote #{quote_id}]: {self.quotes[quote_id]}"
        return None

    def pick_random_quote(self) -> str:
        quote_id = random.randrange(len(list(self.quotes.values())))
        quote = self.quotes[str(quote_id)]
        return f"[Quote #{quote_id}]: {quote}"
