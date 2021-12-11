import os
import re
import srcomapi
from datetime import date
from utils.utils import debugPrint

# enable these for debugging src.py separately from a live bot
# import asyncio
# os.environ['SRC_USER'] = "Phantom5800"
# def debugPrint(value): print(value)

class SrcomApi:
    def __init__(self, srcUser: str):
        self.api = srcomapi.SpeedrunCom()
        self.category_prog = re.compile(r"(.*) (?:\[([^]]+)\])")

        if len(srcUser) > 0:
            user_results = self.api.search(srcomapi.datatypes.User, {"name": srcUser})
            if len(user_results) > 0:
                self.srcuser = user_results[0]
                print(f"Loading personal bests from speedrun.com for {srcUser} ...")
                self.personal_bests = self.srcuser.personal_bests
                print(f"Initialized speedrun.com API for {srcUser}")

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
    Get a list of games available on speedrun.com.
    '''
    def get_games(self) -> list:
        game_list = []
        for run in self.personal_bests:
            if run['run'].level is not None:
                continue
            game_obj = self.api.get_game(run['run'].game)
            gamename = game_obj.name
            if gamename not in game_list and "Category Extensions" not in gamename:
                game_list.append(gamename)
        return game_list

    '''
    Get a list of all categories for a given game.
    '''
    def get_categories(self, game: str) -> list:
        category_list = []
        debugPrint(f"Searching for categories in {game}")

        for run in self.personal_bests:
            if run['run'].level is not None:
                continue
            game_obj = self.api.get_game(run['run'].game)
            gamename = game_obj.name
            # if the run we are looking at, is the correct game
            if game.lower() == gamename.lower() or f"{game} Category Extensions".lower() == gamename.lower():
                debugPrint(f"Found run for {game}")
                game_category = list(filter(lambda cat: cat.data['id'] == run['run'].category, game_obj.categories))
                # if category was found, it should be valid for the query
                if game_category is not None and len(game_category) > 0:
                    category_name = game_category[0].data['name']
                    debugPrint(f"Found category {category_name} for {game}")
                    category_list.append(category_name)

                    # append variables to category name
                    variable_types = game_category[0].variables
                    variables = []

                    # get information about variables
                    run_vars = run['run'].data['values']
                    for variable in variable_types:
                        if variable.data['id'] in run_vars:
                            run_value_id = run_vars[variable.data['id']]
                            run_value = variable.values['values'][run_value_id]['label']
                            variables.append(run_value)
                            category_list[len(category_list) - 1] += f" [{run_value}]"
                    category_list[len(category_list) - 1] = category_list[len(category_list) - 1].replace("] [", ", ")

        return category_list

    '''
    Get the PB for a desired game and category if it exists.
    TODO: Cache results to improve lookup for subsequent searches.
    '''
    def get_pb(self, game: str, category: str, disable_discord_embed: bool = False) -> str:
        category_list = []
        time = "[N/A]"
        vod_link = ""
        found_game = False

        debugPrint(f"[Get PB] Searching for: {game} - {category}")

        matches = self.category_prog.match(category)
        category_vars = []
        if matches is not None:
            category = matches.groups()[0]
            category_vars = matches.groups()[1].split(',')

            # remove extrenuous whitespace from variables
            for i, s in enumerate(category_vars):
                category_vars[i] = s.strip()

        for run in self.personal_bests:
            # ignore ILs
            if run['run'].level is not None:
                continue

            game_obj = self.api.get_game(run['run'].game)
            gamename = game_obj.name
            # if the run we are looking at, is the correct game
            if game.lower() == gamename.lower() or f"{game} Category Extensions".lower() == gamename.lower():
                found_game = True
                if game.lower() == gamename.lower():
                    game = gamename # adjust for proper capitalization
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
                    variable_types = game_category[0].variables
                    variables = []

                    debugPrint(f"[Get PB] Found category match: {category_name}")

                    # get information about variables
                    run_vars = run['run'].data['values']
                    for variable in variable_types:
                        if variable.data['id'] in run_vars:
                            run_value_id = run_vars[variable.data['id']]
                            run_value = variable.values['values'][run_value_id]['label']
                            debugPrint(run_value)
                            if run_value in category_vars:
                                variables.append(run_value)
                            category_list[len(category_list) - 1] += f" [{run_value}]"
                    category_list[len(category_list) - 1] = category_list[len(category_list) - 1].replace("] [", ", ")

                    debugPrint(category_vars)

                    # check if a run was found that matched all the given variables
                    if len(variables) == len(category_vars):
                        debugPrint(f"[Get PB] Found variable match: {category_name} - {variables}")
                        # overwrite the capitalization input by the user
                        if category_name.lower() == category.lower():
                            debugPrint(f"[Get PB] Overwriting {category} with {category_name}")
                            category = category_name
                        # log time and video link
                        time = self.format_time(run['run'].times['primary'])
                        if disable_discord_embed:
                            vod_link = f"<{run['run'].videos['links'][0]['uri']}>"
                        else:
                            vod_link = run['run'].videos['links'][0]['uri']

        # if no runs found
        if found_game == False:
            return f"{os.environ['TWITCH_CHANNEL']} does not have any speedruns of {game}"
        # if there's only one category, don't need it specified
        elif len(category_list) == 1:
            debugPrint(f"[Get PB] Only found one run: {game} - {category_list[0]}")
            return f"{game} - {category_list[0]}: {time} {vod_link}"
        # if no category specified, return a list of categories
        elif category == "":
            return f"Please specify a category for {game}: {str(category_list)}"
        # return the PB for the game and category specified
        else:
            if len(category_vars) > 0:
                debugPrint(f"[Get PB] Returning {game} - {category} {category_vars}")
                return f"{game} - {category} {category_vars}: {time} {vod_link}"
            else:
                debugPrint(f"[Get PB] Returning {game} - {category}")
                return f"{game} - {category}: {time} {vod_link}"

async def main():
    src = SrcomApi()
    #response = src.get_pb("Super Mario 3D World + Bowser's Fury", "Super Mario 3D World") # return's Any%
    #response = src.get_pb("Super Mario 3D World + Bowser's Fury", "Super Mario 3D World [243 Stars]")
    response = src.get_pb("Paper Mario", "Glitchless [N64]")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())