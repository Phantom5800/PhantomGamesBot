import markovify

class MarkovHandler:
    def __init__(self):
        with open("./commands/resources/markov.txt", "r") as f:
            text = f.read()
            # state_size=1 is complete nonsense, 2 makes more ... real sentences, 3 is not random enough
            state_size = 2
            self.text_model = markovify.NewlineText(text, state_size=state_size)
            self.text_model.compile(inplace=True)

            print(self.text_model.to_dict()["state_size"])
            print(f"Possible starting words: {[key[state_size - 1] for key in self.text_model.chain.model.keys() if '___BEGIN__' in key]}")
    
    def get_markov_string(self, include_word=None, max_words=None):
        output = None
        if include_word:
            output = self.text_model.make_sentence_with_start(include_word, False, tries=200, max_overlap_ratio=0.65, max_words=max_words)
        else:
            output = self.text_model.make_sentence(tries=200, max_overlap_ratio=0.65, max_words=max_words)
        return output
