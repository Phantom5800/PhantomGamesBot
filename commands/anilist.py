from AnilistPython import Anilist as _anilist
from datetime import date
import random

class Anilist:
    def __init__(self):
        self.anilist = _anilist()

    def getRandomAnime(self) -> str:
        year = random.randint(1965, date.today().year)
        return self.getRandomAnimeByYear(year)

    def getRandomAnimeByYear(self, year: int) -> str:
        anime = self.anilist.search_anime(year=str(year))
        random_anime = anime[random.randrange(len(anime))]
        # re-roll random anime until you don't get hentai lol
        while "Hentai" in random_anime["genres"] or random_anime["name_english"] is None:
            random_anime = anime[random.randrange(len(anime))]
        return random_anime["name_english"]
