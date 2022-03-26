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
        random_anime = None
        name = None
        # re-roll random anime until you don't get hentai lol
        while name is None or "Hentai" in random_anime["genres"]:
            random_anime = anime[random.randrange(len(anime))]
            name = random_anime["name_english"] if random_anime["name_english"] is not None else random_anime["name_romaji"]
        return name
