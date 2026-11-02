from datetime import datetime
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
        self.text_model = markovify.NewlineText(logtext, state_size=state_size)
        self.text_model.compile(inplace=True)

        # backup with a lower state size in case the more interesting one fails
        self.backup_text = markovify.NewlineText(logtext, state_size=state_size-1)
        self.backup_text.compile(inplace=True)

        print(f"State Size: {self.text_model.to_dict()['state_size']}")
        #print(f"Possible starting words: {[key[state_size - 1] for key in self.text_model.chain.model.keys() if '___BEGIN__' in key]}")
    
    def _get_markov_string(self, *, 
                           include_word=None, 
                           attempts=300,
                           min_words=10,
                           max_overlap_ratio=0.7,
                           max_length=None) -> str:
        output = None
        kwargs = {
            "tries": attempts,
            "max_overlap_ratio": max_overlap_ratio,
            "min_words": min_words
        }

        if include_word:
            output = self.text_model.make_sentence_with_start(include_word, False, **kwargs)
        else:
            output = self.text_model.make_short_sentence(max_chars=max_length, **kwargs)

        if not output:
            output = self.backup_text.make_short_sentence(max_chars=max_length, **kwargs)
        return output

    def get_markov_string(self, *, include_word=None, max_length=None, log=True) -> str:
        output = self._get_markov_string(include_word=include_word, max_length=max_length)

        # only log messages that are marked for logging
        if log:
            directory = "./commands/resources/markov/generated/"
            with open(os.path.join(directory, f"generated-{datetime.now().year}.txt"), "a+", encoding="utf-8") as f:
                try:
                    f.write(f"[{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}] @ {output}\n")
                except:
                    print("[Markov] Failed to log generated message")

        return output
