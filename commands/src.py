import os
import re
import srcomapi
from datetime import date

class SrcomApi:
    def __init__(self):
        self.api = srcomapi.SpeedrunCom()

        user_results = self.api.search(srcomapi.datatypes.User, {"name": os.environ['SRC_USER']})
        if len(user_results) > 0:
            self.srcuser = user_results[0]
            print(f"Initialized speedrun.com API for {os.environ['SRC_USER']}")

    def tryParseInt(self, re_result) -> int:
        if re_result is not None and re_result.lastindex > 0:
            result_string = re_result[1]
            # drop milliseconds from the seconds component
            if '.' in result_string:
                result_string = result_string[0:result_string.index('.')]
            try:
                return int(result_string)
            except ValueError:
                return 0
        return 0

    def format_time(self, src_time: str) -> str:
        hour_re = r'([0-9]*)H'
        minutes_re = r'([0-9]*)M'
        seconds_re = r'([.0-9]*)S'
        
        hours = self.tryParseInt(re.search(hour_re, src_time))
        minutes = self.tryParseInt(re.search(minutes_re, src_time))
        seconds = self.tryParseInt(re.search(seconds_re, src_time))

        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        elif minutes > 0:
            return f"{minutes}:{seconds:02}"
        else:
            return f"{seconds}"

    '''
    Get the PB for a desired game and category if it exists
    '''
    async def get_pb(self, game: str, category: str) -> str:
        category_list = []
        time = "[No time submitted]"
        vod_link = ""
        found_game = False
        for run in self.srcuser.personal_bests:
            game_obj = self.api.get_game(run['run'].game)
            gamename = game_obj.name
            # if the run we are looking at, is the correct game
            if game == gamename or f"{game} Category Extensions" == gamename:
                found_game = True
                # have to check every category because run only contains category id
                for cat in game_obj.categories:
                    # find the category for this run
                    if run['run'].category == cat.data['id']:
                        game_cat = cat.data['name']
                        category_list.append(game_cat)
                        # if user was looking for this category, store time and video
                        # if no time and video have been stored, take this one just in case
                        if game_cat == category or vod_link == "":
                            time = self.format_time(run['run'].times['primary'])
                            vod_link = run['run'].videos['links'][0]['uri']

        # if no runs found
        if found_game == False:
            return f"{os.environ['SRC_USER']} does not have any speedruns of {game}"
        # if there's only one category, don't need it specified
        elif len(category_list) == 1:
            return f"{game} - {category_list[0]}: {time} {vod_link}"
        # if no category specified, return a list of categories
        elif category == "":
            return f"Please specify a category for {game}: {str(category_list)}"
        # return the PB for the game and category specified
        else:
            return f"{game} - {category}: {time} {vod_link}"
