"""This module exposes user configurable settings"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from builtins import super

standard_library.install_aliases()

from json import loads
from os import getenv, makedirs
from os.path import isfile, dirname
from io import open
from munch import Munch

from gobble import settings as config_module


# Importing modules other than settings here will cause circular imports


class Config(Munch):
    """Gobble user configurable settings"""

    def __init__(self, defaults):
        super(Config, self).__init__(**defaults)
        self.update(self.load())

    def load(self):
        if not isfile(self.CONFIG_FILE):
            return {}
        with open(self.CONFIG_FILE) as json:
            return loads(json.read())

    def save(self):
        folder = dirname(self.CONFIG_FILE)
        makedirs(folder, exist_ok=True)
        with open(self.CONFIG_FILE, 'w+', encoding='utf-8') as file:
            file.write(self.toJSON())
        return self


_default_mode = getenv('GOBBLE_MODE', 'Production')
_default_class = getattr(config_module, _default_mode)
_default_dict = {key: getattr(_default_class, key)
                 for key in dir(_default_class)
                 if key.isupper()}

config = Config(_default_dict)


