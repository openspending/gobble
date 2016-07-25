"""This module exposes user configurable settings"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from builtins import super
from past.types import unicode

standard_library.install_aliases()

from json import loads, dumps
from os import getenv, makedirs
from os.path import isfile, dirname
import io

from gobble import settings as config_module


# Importing modules other than settings here will cause circular imports


class Config(dict):
    """Gobble user configurable settings"""

    def __init__(self, defaults):
        super(Config, self).__init__(**defaults)
        self.update(self.load())

    def __getattr__(self, item):
        if item.isupper():
            return self[item]

    def load(self):
        if not isfile(self.CONFIG_FILE):
            return {}
        with io.open(self.CONFIG_FILE) as json:
            return loads(json.read())

    def save(self):
        makedirs(dirname(self.CONFIG_FILE))
        with io.open(self.CONFIG_FILE, 'w+', encoding='utf-8') as file:
            # What a freaking mess dude... I hate python 2 with a passion
            file.write(unicode(dumps(self, ensure_ascii=False, indent=2)))
        return self


_default_mode = getenv('GOBBLE_MODE', 'Production')
_default_class = getattr(config_module, _default_mode)
_default_dict = {key: getattr(_default_class, key)
                 for key in dir(_default_class)
                 if key.isupper()}

config = Config(_default_dict)


# TODO: find a home the console output decorator

def to_console(method):
    def wrapper(self, *args, **kwwargs):
        result = method(self, *args, **kwwargs)
        result = dict(result)
        if self.in_shell:
            json = dumps(result,
                         ensure_ascii=False,
                         indent=4)
            print(json)
        return result
    return wrapper

