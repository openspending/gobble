"""Test the logger module"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from logging import FileHandler, StreamHandler, Logger, LogRecord
from future import standard_library

standard_library.install_aliases()

from gobble.logger import log, MultilineFilter


def test_gobble_logger_exists_and_has_correct_name():
    assert isinstance(log, Logger)
    assert log.name == 'Gobble'


def test_logger_has_multiline_filter():
    any(list(map(lambda x: isinstance(x, MultilineFilter), log.filters)))


def test_logger_has_at_least_one_handler():
    file = any(list(map(lambda x: isinstance(x, FileHandler), log.handlers)))
    cons = any(list(map(lambda x: isinstance(x, StreamHandler), log.handlers)))
    assert any((file, cons))


def test_multifile_filter_catches_multiline_records():
    multiline = LogRecord('foo', 0, 'bar', 0, '\n', (), 'spam')
    MultilineFilter().filter(multiline) is False
