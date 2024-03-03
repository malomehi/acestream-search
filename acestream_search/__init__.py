# -*- coding: utf-8 -*-

import logging
import requests


requests.packages.urllib3.disable_warnings()

logger = logging.getLogger()
logger.setLevel('INFO')
format = '[%(levelname)s] %(message)s'
logging.basicConfig(format=format)
