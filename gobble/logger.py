"""A simple logger that logs to file and console"""


from logging import getLogger, FileHandler, StreamHandler, DEBUG, Formatter


from gobble.configuration import config


def _configure_logger(name):
    logger = getLogger(name)
    logger.setLevel(DEBUG)

    if config.LOG_LEVEL_FILE:
        file = FileHandler(config.LOG_FILE)
        file.setLevel(config.LOG_LEVEL_FILE)
        file.setFormatter(Formatter(config.LOG_FORMAT_FILE))
        logger.addHandler(file)

    if config.LOG_LEVEL_CONSOLE:
        stream = StreamHandler()
        stream.setLevel(config.LOG_LEVEL_CONSOLE)
        stream.setFormatter(Formatter(config.LOG_FORMAT_CONSOLE))
        logger.addHandler(stream)

    return logger


log = _configure_logger('Gobble')
