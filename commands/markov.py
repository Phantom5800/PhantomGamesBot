import markovify

class MarkovHandler:
    def __init__(self):
        with open("./commands/resources/markov.txt", "r") as f:
            text = f.read()
            # state_size=1 is complete nonsense, 2 makes more ... real sentences, 3 is not random enough
            state_size = 3
            self.text_model = markovify.NewlineText(text, state_size=state_size)
            self.text_model.compile(inplace=True)

            # backup with a lower state size in case the more interesting one fails
            self.backup_text = markovify.NewlineText(text, state_size=state_size-1)
            self.backup_text.compile(inplace=True)

            print(self.text_model.to_dict()["state_size"])
            print(f"Possible starting words: {[key[state_size - 1] for key in self.text_model.chain.model.keys() if '___BEGIN__' in key]}")
    
    def get_markov_string(self, include_word=None, max_words=None):
        overlap = 0.65
        attempts = 300
        output = None

        # if include_word:
        #     output = self.text_model.make_sentence_with_start(include_word, False, tries=attempts, max_overlap_ratio=overlap, max_words=max_words)
        # else:
        #     output = self.text_model.make_sentence(tries=attempts, max_overlap_ratio=overlap, max_words=max_words)

        if not output:
            output = self.backup_text.make_sentence(tries=attempts, max_overlap_ratio=overlap, max_words=max_words)
        return output
