import os
import random
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
        self.srcUser = srcUser

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

    def test_game(self, game: str, category: str):
        game_obj = self.api.search(srcomapi.datatypes.Game, {"name": game})[0]
        for c in game_obj.categories:
            if c.name == category:
                print(game_obj.categories)
                print(f"{game} - {category}: {vars(c)}")
                return

    '''
    Get a random game for a given src user
    '''
    def get_random_user_game(self, user: str) -> str:
        try:
            user_results = self.api.search(srcomapi.datatypes.User, {"name": user, "max": 100})
            if len(user_results) > 0:
                found_user = False
                for u in user_results:
                    if u.name.lower() == user.lower():
                        user = u
                        found_user = True
                        break
                if found_user:
                    if len(user.personal_bests) > 0:
                        random_run = user.personal_bests[random.randrange(len(user.personal_bests))]

                        # do not take an IL unless it takes a while to find a real game ...
                        il_attempts = 0
                        while random_run['run'].level is not None and il_attempts < 10:
                            random_run = user.personal_bests[random.randrange(len(user.personal_bests))]
                            il_attempts += 1

                        game_obj = self.api.get_game(random_run['run'].game)
                        game_categories = list(filter(lambda cat: cat.data['id'] == random_run['run'].category, game_obj.categories))
                        random_category = game_categories[random.randrange(len(game_categories))]
                        category_name = random_category.data['name']

                        variable_types = random_category.variables
                        if len(variable_types) > 0:
                            varstr = ""
                            run_vars = random_run['run'].data['values']
                            for variable in variable_types:
                                if variable.data['id'] in run_vars:
                                    run_value_id = run_vars[variable.data['id']]
                                    run_value = variable.values['values'][run_value_id]['label']
                                    varstr += f" [{run_value}]"
                            varstr = varstr.replace("] [", ", ")
                            category_name += varstr

                        return f"{game_obj.name} - {category_name}"
                    return f"anything"
        except:
            print("src 404 error")
        
        return f"existing (it seems they don't have a profile on speedrun.com)"

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
            return f"{self.srcUser} does not have any speedruns of {game}"
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
