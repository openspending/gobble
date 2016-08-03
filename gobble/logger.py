"""A simple logger that logs to file and console"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
from logging import (getLogger,
                     FileHandler,
                     StreamHandler,
                     DEBUG,
                     Formatter,
                     Filter)

from gobble.config import settings, GOBBLE_MODE

standard_library.install_aliases()


class MultilineFilter(Filter):
    """Split a multi-line message over several log records"""

    # http://stackoverflow.com/questions/22934616
    # This is not considered good practice but it
    # preserves indentation and improves readability.
    # I log the same information twice anyway.

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

    if settings.FILE_LOG_LEVEL:
        file = FileHandler(settings.LOG_FILE)
        file.setLevel(settings.FILE_LOG_LEVEL)
        file.setFormatter(Formatter(settings.FILE_LOG_FORMAT))
        logger.addHandler(file)

    if settings.CONSOLE_LOG_LEVEL:
        stream = StreamHandler()
        stream.setLevel(settings.CONSOLE_LOG_LEVEL)
        stream.setFormatter(Formatter(settings.CONSOLE_LOG_FORMAT))
        logger.addHandler(stream)

    return logger


log = _configure_logger('Gobble')


log.debug('Gobble is running in %s mode', GOBBLE_MODE)


for key, value in vars(settings).items():
    if key.isupper():
        log.debug('%s = %s', key, value)


