#!/usr/bin/python3

import logging

#Set up logging
logging.basicConfig(filename = "scrape.log",
					level = logging.DEBUG,
					format='%(levelname)s - %(asctime)s - %(funcName)s: %(message)s',
    				datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()