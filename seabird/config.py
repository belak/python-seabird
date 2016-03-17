class Config(dict):
    def from_module(self, module_name):
        module = __import__(module_name)

        for k in dir(module):
            if not k.isupper():
                continue

            self[k] = getattr(module, k)

    @property
    def networks(self):
        networks = self.get('NETWORKS')
        if networks is None:
            return [self]

        ret = []
        for network in networks:
            conf = self.copy()
            conf.update(network)
            ret.append(conf)

        return ret
