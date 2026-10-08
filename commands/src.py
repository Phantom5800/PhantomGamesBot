import random
import re
import srcomapi
from datetime import date

class SrcomApi:
    def __init__(self):
        self.api = srcomapi.SpeedrunCom()
        self.category_prog = re.compile(r"(.*) (?:\[([^]]+)\])")

    '''
    Test function to get a random category for a game
    '''
    def get_random_category(self, game: str) -> str:
        try:
            random_game = self.api.search(srcomapi.datatypes.Game, {"name": game})
            if random_game is None or len(random_game) == 0:
                return self.get_random_game()

            random_game = random_game[random.randrange(len(random_game))]
            random_category = random_game.categories[random.randrange(len(random_game.categories))]
            # try a new category until we find one that gives a unique uri?
            attempts = 0
            while random_game.weblink == random_category.weblink:
                random_category = random_game.categories[random.randrange(len(random_game.categories))]
                attempts += 1
                if attempts > 50:
                    break
            result = f"{random_game.name} - {random_category.name}"
            print(f"{result}: {random_category.weblink}")

            return result
        except:
            print("src 404 error")
            return "speedrun.com returned 404, try again later maybe? idk"

    '''
    Returns a random game listed on speedrun.com
    '''
    def get_random_game(self) -> str:
        try:
            release_year = random.randint(1985, date.today().year-1)
            query_result = self.api.search(srcomapi.datatypes.Game, 
                {
                    "_bulk": True, 
                    "max": 5000,
                    "released": release_year
                })
            random_game = query_result[random.randrange(len(query_result))]
            random_category = random_game.categories[random.randrange(len(random_game.categories))]
            # try a new category until we find one that gives a unique uri?
            attempts = 0
            while random_game.weblink == random_category.weblink:
                random_category = random_game.categories[random.randrange(len(random_game.categories))]
                attempts += 1
                if attempts > 50:
                    break
            result = f"{random_game.name} - {random_category.name}"
            print(f"{result}: {random_category.weblink}")

            return result
        except:
            print("src 404 error")
            return "speedrun.com returned 404, try again later maybe? idk"
