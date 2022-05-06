import markovify

class MarkovHandler:
    def __init__(self):
        with open("./commands/resources/markov.txt", "r") as f:
            text = f.read()
            self.text_model = markovify.NewlineText(text)
            self.text_model.compile(inplace=True)

            print(self.text_model.to_dict()["state_size"])
    
    def getMarkovString(self):
        output = self.text_model.make_sentence(tries=100)
        return output