"""A simple logger that logs to file and console"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from json import dumps

from future import standard_library
standard_library.install_aliases()

from logging import (getLogger,
                     FileHandler,
                     StreamHandler,
                     DEBUG,
                     Formatter,
                     Filter)

from gobble.configuration import config


def sdumps(dict_):
    """A thin py2/py3 compatibilty wrapper for JSON dumps"""
    return dumps(dict_, ensure_ascii=False, indent=2)


class MultilineFilter(Filter):
    """Split a multi-line message over several log records"""

    # http://stackoverflow.com/questions/22934616
    # This is not considered good practice but it
    # preserves indentation and improves readability.

    # TODO: display the correct (calling) module in the log record

    def filter(self, record):
        message = record.getMessage()

        if '\n' not in message:
            return True

        for line in message.split('\n'):
            log.debug(line)
        return False


def _configure_logger(name):
    logger = getLogger(name)
    multiline = MultilineFilter()

    logger.addFilter(multiline)
    logger.setLevel(DEBUG)

    if config.FILE_LOG_LEVEL:
        file = FileHandler(config.LOG_FILE)
        file.setLevel(config.FILE_LOG_LEVEL)
        file.setFormatter(Formatter(config.FILE_LOG_FORMAT))
        logger.addHandler(file)

    if config.CONSOLE_LOG_LEVEL:
        stream = StreamHandler()
        stream.setLevel(config.CONSOLE_LOG_LEVEL)
        stream.setFormatter(Formatter(config.CONSOLE_LOG_FORMAT))
        logger.addHandler(stream)

    return logger


log = _configure_logger('Gobble')
