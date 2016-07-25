"""Test the logger module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from gobble.logger import log


def test_gobble_logger_exists():
    assert log.name == 'Gobble'
