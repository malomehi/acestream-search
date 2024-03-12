# -*- coding: utf-8 -*-

import logging
import platform


COLORS = {
    'blue': '\x1b[34;20m',
    'light_blue': '\x1b[94;20m',
    'yellow': '\x1b[33;20m',
    'red': '\x1b[31;20m',
    'bold_red': '\x1b[31;1m',
    'reset': '\x1b[0m'
}
FORMAT = '[%(levelname)s] %(message)s'
RESET = '\x1b[0m'
FORMATS = {
    logging.DEBUG: COLORS['blue'] + FORMAT + RESET,
    logging.INFO: COLORS['light_blue'] + FORMAT + RESET,
    logging.WARNING: COLORS['yellow'] + FORMAT + RESET,
    logging.ERROR: COLORS['red'] + FORMAT + RESET,
    logging.CRITICAL: COLORS['bold_red'] + FORMAT + RESET
}


class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = FORMATS.get(
            record.levelno
        ) if platform.system() != 'Windows' else FORMAT
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)
