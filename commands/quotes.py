import json
from copy import deepcopy
from datetime import datetime
import locale
import random

class QuoteHandler:
    async def load_quotes(self):
        with open('./commands/resources/quotes.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.quotes = deepcopy(data)
                print(self.quotes)
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load quotes from JSON")
                return

    async def save_quotes(self):
        with open('./commands/resources/quotes.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.quotes)
            json_file.write(json_str)

    async def add_quote(self, quote: str, game: str, ctx):
        new_id = len(list(self.quotes.values()))
        date = datetime.now().strftime("%m/%d/%Y")
        quote_str = f"{quote} [{game}] [{date}]"
        self.quotes[str(new_id)] = quote_str
        await self.save_quotes()
        await ctx.send(f"Added [Quote #{new_id}] -> {quote_str}")

    async def edit_quote(self, quote_id: int, quote: str, ctx):
        self.quotes[str(quote_id)] = quote
        await self.save_quotes()
        await ctx.send(f"Edited [Quote #{new_id}] -> {quote_str}")

    async def pick_specific_quote(self, quote_id: str, ctx):
        if quote_id in self.quotes:
            await ctx.send(f"[Quote #{quote_id}]: {self.quotes[quote_id]}")

    async def pick_random_quote(self, ctx):
        quote_id = random.randrange(len(list(self.quotes.values())))
        quote = self.quotes[str(quote_id)]
        await ctx.send(f"[Quote #{quote_id}]: {quote}")
