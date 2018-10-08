class Config(dict):
    def from_module(self, module_name):
        module = __import__(module_name)

        for k in dir(module):
            if not k.isupper():
                continue

            self[k] = getattr(module, k)
