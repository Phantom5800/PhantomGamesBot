import os
import re
import srcomapi
from datetime import date
from utils.utils import debugPrint

# enable these for debugging src.py separately from a live bot
#import asyncio
#os.environ['SRC_USER'] = "Phantom5800"
#def debugPrint(value): print(value)

class SrcomApi:
    def __init__(self):
        self.api = srcomapi.SpeedrunCom()

        if len(os.environ['SRC_USER']) > 0:
            user_results = self.api.search(srcomapi.datatypes.User, {"name": os.environ['SRC_USER']})
            if len(user_results) > 0:
                self.srcuser = user_results[0]
                print(f"Loading personal bests from speedrun.com for {os.environ['SRC_USER']} ...")
                self.personal_bests = self.srcuser.personal_bests
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
        # TODO: don't drop the milliseconds if they exist

        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        elif minutes > 0:
            return f"{minutes}:{seconds:02}"
        else:
            return f"{seconds}"

    '''
    Get the PB for a desired game and category if it exists.
    TODO: Cache results to improve lookup for subsequent searches.
    '''
    def get_pb(self, game: str, category: str) -> str:
        category_list = []
        time = "[N/A]"
        vod_link = ""
        found_game = False
        for run in self.personal_bests:
            game_obj = self.api.get_game(run['run'].game)
            gamename = game_obj.name
            # if the run we are looking at, is the correct game
            if game.lower() == gamename.lower() or f"{game} Category Extensions".lower() == gamename.lower():
                found_game = True
                debugPrint(f"[Get PB] Found game: {gamename}")
                # search list of categories for the one matching this current run
                # filter out anything that does not match {category} if no run has been logged yet
                game_category = list(filter(lambda cat: 
                        cat.data['id'] == run['run'].category and
                        (cat.data['name'].lower() == category.lower() or vod_link == "" or category == "")
                        , game_obj.categories))
                # if category was found, it should be valid for the query
                if game_category is not None and len(game_category) > 0:
                    category_name = game_category[0].data['name']
                    category_list.append(category_name)
                    variables = game_category[0].variables
                    debugPrint(f"[Get PB] Found category: {category_name} - {variables}")
                    # overwrite the capitalization input by the user
                    if category_name.lower() == category.lower():
                        debugPrint(f"[Get PB] Overwriting {category} with {category_name}")
                        category = category_name
                    # log time and video link
                    time = self.format_time(run['run'].times['primary'])
                    vod_link = run['run'].videos['links'][0]['uri']

        # if no runs found
        if found_game == False:
            return f"{os.environ['CHANNEL']} does not have any speedruns of {game}"
        # if there's only one category, don't need it specified
        elif len(category_list) == 1:
            debugPrint(f"[Get PB] Only found one run: {game} - {category_list[0]}")
            return f"{game} - {category_list[0]}: {time} {vod_link}"
        # if no category specified, return a list of categories
        elif category == "":
            return f"Please specify a category for {game}: {str(category_list)}"
        # return the PB for the game and category specified
        else:
            debugPrint(f"[Get PB] Returning {game} - {category}")
            return f"{game} - {category}: {time} {vod_link}"

async def main():
    src = SrcomApi()
    #response = await src.get_pb("Super Mario 3D World + Bowser's Fury", "")
    response = await src.get_pb("Paper Mario", "")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())