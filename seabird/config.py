from importlib import import_module


class BotConfig(dict):
    def from_module(self, module_name):
        module = import_module(module_name)
        for k, v in module.__dict__.items():
            # Skip any private variables
            if k.startswith('_'):
                continue

            self[k] = v
