class AliasDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.aliases = {}

    def __getitem__(self, key):
        return dict.__getitem__(self, self.aliases.get(key, key))

    def __setitem__(self, key, value):
        return dict.__setitem__(self, self.aliases.get(key, key), value)

    def __contains__(self, key):
        return dict.__contains__(self, self.aliases.get(key, key))

    def add_alias(self, key, alias):
        self.aliases[alias] = key
