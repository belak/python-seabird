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
            return {'main': self}

        ret = {}

        if isinstance(networks, dict):
            for name, network in networks.items():
                conf = self.copy()
                conf.update(network)
                ret[name] = conf
        else:
            for network in networks:
                conf = self.copy()
                conf.update(network)
                ret[conf['id']] = conf

        return ret
