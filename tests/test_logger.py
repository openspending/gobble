"""Test the logger module"""

from gobble.logger import log


def test_gobble_logger_exists():
    assert log.name == 'Gobble'
