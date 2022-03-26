from AnilistPython import Anilist as _anilist
from datetime import date
import random

class Anilist:
    def __init__(self):
        self.anilist = _anilist()

    def getAnimeByName(self, anime_name: str):
        try:
            return self.anilist.get_anime(anime_name=anime_name)
        except:
            return None

    def getRandomAnimeName(self):
        year = random.randint(1965, date.today().year)
        return self.getRandomAnime()[0]

    def getRandomAnime(self):
        year = random.randint(1965, date.today().year)
        return self.getRandomAnimeByYear(year)

    def getRandomAnimeByYear(self, year: int):
        anime = self.anilist.search_anime(year=str(year))
        random_anime = None
        name = None
        # re-roll random anime until you don't get hentai lol
        while name is None or "Hentai" in random_anime["genres"]:
            random_anime = anime[random.randrange(len(anime))]
            name = random_anime["name_english"] if random_anime["name_english"] is not None else random_anime["name_romaji"]
        return name, random_anime

    def formatDiscordAnimeEmbed(self, anime_name, discord_embed):
        anime_dict = self.getAnimeByName(anime_name)

        eng_name = anime_dict["name_english"]
        jp_name = anime_dict["name_romaji"]
        desc = anime_dict['desc']
        starting_time = anime_dict["starting_time"]
        ending_time = anime_dict["ending_time"]
        cover_image = anime_dict["cover_image"]
        airing_format = anime_dict["airing_format"]
        airing_status = anime_dict["airing_status"]
        airing_ep = anime_dict["airing_episodes"]
        season = anime_dict["season"]
        genres = anime_dict["genres"]
        next_airing_ep = anime_dict["next_airing_ep"]
        anime_link = f'https://anilist.co/anime/{self.anilist.get_anime_id(anime_name)}/'

        #parse genres
        genres_new = ''
        count = 1
        for i in genres:
            if count != len(genres):
                genres_new += f'{i}, '
            else:
                genres_new += f'{i}'
            count += 1

        #parse time
        next_ep_string = ''
        try:
            initial_time = next_airing_ep['timeUntilAiring']
            mins, secs = divmod(initial_time, 60)
            hours, mins = divmod(mins, 60)
            days, hours = divmod(hours, 24)
            timer = f'{days} days {hours} hours {mins} mins {secs} secs'
            next_ep_num = next_airing_ep['episode']
            next_ep_string = f'Episode {next_ep_num} is releasing in {timer}!\
                            \n\n[{jp_name} AniList Page]({anime_link})'
        except:
            next_ep_string = f"This anime's release date has not been confirmed!\
                            \n\n[{jp_name} AniList Page]({anime_link})"

        #parse desc
        if desc != None and len(desc) != 0:
            desc = desc.strip().replace('<br>', '')
            desc = desc.strip().replace('<i>', '')
            desc = desc.strip().replace('</i>', '')
        
        key_list = [eng_name, jp_name, desc, starting_time, ending_time, cover_image, airing_format, airing_status, airing_ep, season, genres_new, next_ep_string]
        info = self.embedValueCheck(key_list)

        discord_embed.set_image(url=cover_image)
        discord_embed.add_field(name="Synopsis", value=info[2], inline=False)
        discord_embed.add_field(name="Airing Date", value=info[3], inline=True)
        discord_embed.add_field(name="Ending Date", value=info[4], inline=True)
        discord_embed.add_field(name="Season", value=info[9], inline=True)

        try:
            episodes = int(airing_ep)

            if episodes > 1:
                discord_embed.add_field(name="Airing Format", value=f"{info[6]} ({airing_ep} episodes)", inline=True)
            else:
                discord_embed.add_field(name="Airing Format", value=f"{info[6]} ({airing_ep} episode)", inline=True)

        except:
            discord_embed.add_field(name="Airing Format", value=info[6], inline=True)


        if info[7].upper() == 'FINISHED':
            discord_embed.add_field(name="Airing Status", value=info[7], inline=True)
            discord_embed.add_field(name="Genres", value=info[10], inline=True)
            discord_embed.add_field(name="Next Episode ~", value=f"The anime has finished airing!\n\n[{jp_name} AniList Page]({anime_link})\n[AnilistPython Documentation](https://github.com/ReZeroE/AnilistPython)", inline=False)

        else:
            discord_embed.add_field(name="Airing Status", value=info[7], inline=True)
            discord_embed.add_field(name="Genres", value=info[10], inline=True)
            discord_embed.add_field(name="Next Episode ~", value=info[11], inline=False)
        return discord_embed

    def embedValueCheck(self, key_list) -> list:
        MAXLEN = 1024
        index = 0
        for i in key_list:
            # Null value check ===============================================
            if i == None:
                key_list[index] = 'Not Available'
            if isinstance(i, str) and len(i) == 0:
                key_list[index] = 'Not Available'

            # Length check ===================================================
            if isinstance(i, str) and len(i) >= MAXLEN:
                toCrop = (len(i) - MAXLEN) + 3
                key_list[index] = i[: -toCrop] + "..."
                        
            index += 1
        return key_list