from datetime import datetime
from random import randint
import markovify
import os

class MarkovHandler:
    def __init__(self):
        logtext = ""

        # iterate over the log files for each year and combine them
        # TODO: make obsolete years pre-compiled markov modules
        directory = "./commands/resources/markov/"
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f):
                print(filename)
                with open(f, "r", encoding="utf-8") as markov_file:
                    line = markov_file.read()
                    delimiter = line.find("] @ ")
                    if delimiter == -1:
                        logtext += line
                    else:
                        logtext += line[delimiter+4:]

        # state_size=1 is complete nonsense, 2 makes more ... real sentences, 3 is not random enough
        state_size = 3
        self.text_models = list()
        for i in range(0, state_size):
            self.text_models.append(markovify.NewlineText(logtext, state_size=i+1))
            self.text_models[-1].compile(inplace=True)

    def _get_markov_string(self, *, 
                           attempts=300,
                           min_words=10,
                           max_overlap_ratio=0.7,
                           max_length=None) -> str:
        kwargs = {
            "tries": attempts,
            "max_overlap_ratio": max_overlap_ratio,
            "min_words": min_words
        }

        # randomly select which model to use
        rand_chance = randint(1, 100)
        if rand_chance <= 10: # 10% chance for complete nonsense
            random_idx = 0
        elif rand_chance <= 50: # 40% chance for more real sentences
            random_idx = 1
        else: # 50% chance for most well constructed sentences
            random_idx = 2

        def _get_markov_string_from_model(model):
            if max_length is None:
                return model.make_sentence(**kwargs)
            else:
                return model.make_short_sentence(max_chars=max_length, **kwargs)

        return _get_markov_string_from_model(self.text_models[random_idx])

    def get_markov_string(self, *, max_length=None, log=True) -> str:
        output = self._get_markov_string(max_length=max_length)

        # only log messages that are marked for logging
        if log:
            directory = "./commands/resources/markov/generated/"
            with open(os.path.join(directory, f"generated-{datetime.now().year}.txt"), "a+", encoding="utf-8") as f:
                try:
                    f.write(f"[{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}] @ {output}\n")
                except:
                    print("[Markov] Failed to log generated message")

        return output
