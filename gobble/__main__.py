"""Command line tools to load data efficiently into Open-Spending"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from click import command
from future import standard_library

standard_library.install_aliases()


@command()
def cli():
    print('Welcome to Gobble!')
