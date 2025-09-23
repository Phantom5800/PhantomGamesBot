from datetime import datetime, timezone
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
    
    def _get_markov_string(self, include_word=None, max_words=None):
        overlap = 0.7
        attempts = 300
        output = None
        min_words = 10

        # if include_word:
        #     output = self.text_model.make_sentence_with_start(include_word, False, tries=attempts, max_overlap_ratio=overlap, min_words=min_words, max_words=max_words)
        # else:
        #     output = self.text_model.make_sentence(tries=attempts, max_overlap_ratio=overlap, min_words=min_words, max_words=max_words)

        if not output:
            output = self.backup_text.make_sentence(tries=attempts, max_overlap_ratio=overlap, min_words=min_words, max_words=max_words)
        return output

    def get_markov_string(self, include_word=None, max_words=None, log=True):
        output = self._get_markov_string(include_word, max_words)

        # only log messages that are marked for logging
        if log:
            directory = "./commands/resources/markov/generated/"
            with open(os.path.join(directory, f"generated-{datetime.now().year}.txt"), "a+", encoding="utf-8") as f:
                try:
                    f.write(f"[{datetime.now()}] @ {output}\n")
                except:
                    print("[Markov] Failed to log generated message")

        return output
