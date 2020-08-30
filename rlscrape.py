#!/usr/bin/python3.8.5

from bs4 import BeautifulSoup
import argparse
import requests
import re
import os
import sys
from setup_logging import logger

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
from tabulate import tabulate



class Webscrape():
	''' Define the details behind the webpage
	'''
	def __init__(self):
		self.webpath = "https://rocketleague.tracker.network/rocket-league/profile"
		#self.webpathmmr = "https://rocketleague.tracker.network/profile/mmr"
		self.latestseason = '14' #need a better way to update this, perhaps dynamically?
		self.rltrackermissing = "We could not find your stats,"
		self.psyonixdisabled = "Psyonix has disabled the Rocket League API"

	def retrieveDataRLTracker(self,gamertag="76561198049122040",platform="steam",seasons=["14"]):
		''' Python BeautifulSoup4 Webscraper to https://rocketleague.tracker.network/ to retrieve gamer data
			gamertag 76561198049122040 = memlo steam id
			platform options are xbl, psn, steam
			returns a dictionary for the gamertag with playlist, mmr, gamesplayed, and rank
		'''
		latestseason = self.latestseason
		#webpathmmr = self.webpathmmr
		webpath = self.webpath
		playerwebpath = "%(webpath)s/%(platform)s/%(gamertag)s/overview" % locals()
		rltrackermissing = self.rltrackermissing
		psyonixdisabled = self.psyonixdisabled
		playerdata = {} # define the playerdata dict
		playerdata[gamertag] = {} # define the gamertag dict
		if '[]' in seasons:
			logger.critical("Season was not set - you should never see this error")
		# create a new Chrome session
		# skip the SSL errors
		# log the errors instead of printing them
		options = webdriver.ChromeOptions()
		options.add_argument('--ignore-certificate-errors-spki-list') # ('--ignore-certificate-errors')
		options.add_experimental_option('excludeSwitches', ['enable-logging'])
		options.add_argument('--ignore-ssl-errors')
		driver = webdriver.Chrome(chrome_options=options)
		driver.implicitly_wait(30)
		driver.get(playerwebpath) # pass player URL into Chrome window
		for season in seasons:
			if self._testSeason(season):
				playerdata[gamertag][season] = {} #define the season dict
				soup = BeautifulSoup(driver.page_source, 'lxml')
				# we should no longer need the chrome window open, so close it now
				# this should reduce memory requirements... hopefully
				driver.close()
				#soup = BeautifulSoup(page.html, 'html.parser')
				if soup.find('div', class_='error-message'):
					logger.error(soup.find('div', class_='error-message').text)
				else:
					try:
						html_table = soup.find('table', class_='trn-table')
						trs = html_table.findAll('tr')
					except(AttributeError):
						logger.error("Could not find required data table for gamertag: %(gamertag)s at url: %(playerwebpath)s" % locals())
					else:
						for tr in trs[1:]: #parse the <tr> within the <table> with the data
							playlist = tr.find('td', class_='name').find('div', class_='playlist').text.strip()
							mmr = tr.find('td', class_='rating').find('div', class_='value').text.strip()
							gp = tr.find('td', class_='matches').find('div', class_='value').text.strip()
							rank = tr.find('td', class_='name').find('div', class_='rank').text.strip()
							# cleanup comma separated values so they're displayed as int, not strings
							if "," in mmr:
								mmr = int(mmr.replace(',' , ''))
							if "," in gp:
								gp = int(gp.replace(',' , ''))
							playerdata[gamertag][season][playlist] = {}
							playerdata[gamertag][season][playlist]['MMR'] = mmr
							playerdata[gamertag][season][playlist]['Games Played'] = gp
							playerdata[gamertag][season][playlist]['Rank'] = rank
		if '{}' in playerdata[gamertag]: #condition to alert if gamertag retrieval was blank
			logger.debug("Gamertag: %(gamertag)s had no data to retrieve" % locals())
		logger.debug("Data retrieval complete for gamertag: %(gamertag)s" % locals()) # a simple measure to make sure we catch every player when a list is ran
		#sys.exit(Page.exec_())
		return playerdata

	def _testSeason(self,season):
		'''True/False to see if season is valid
		1) is a number and is a valid season less than current number'''
		latestseason = self.latestseason
		try:
			if not season.isdigit():
				raise NameError
			if int(season) > int(latestseason):
				raise ValueError
		except ValueError:
			logger.error("Season:%(season)s was higher than Current Season:%(latestseason)s" % locals())
			return False
		except NameError:
			logger.error("Season:%(season)s was not a number" % locals())
			return False
		else:
			return True
					
def singleRun(gamertag,platform,seasons):
	'''Single run of Webscrape.retrieveDataRLTracker'''
	logger.info("Start for gamertag:%(gamertag)s"% locals())
	scrape = Webscrape()
	data = scrape.retrieveDataRLTracker(gamertag=gamertag,platform=platform,seasons=seasons)
	if data is not None:
		pprint(data)
		logger.info("Finish for gamertag:%(gamertag)s"% locals())

if __name__ == "__main__":
	'''Run locally to this script'''

	from pprint import pprint # pprint is cool
	#Pass arguments for name and platform
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-p', action='store', dest='platform', help='platform options. Example: steam', choices=('steam','psn','xbl'), default='steam')
	parser.add_argument('-g', action='store', dest='gamertag', help='your gamertag', default='76561198049122040')
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
	
	results = parser.parse_args()
	platform = results.platform
	gamertag = results.gamertag
	seasons = results.seasons
	
	singleRun(gamertag,platform,seasons)

'''Idea
class Gamer(object):
	"""docstring for ClassName"""
	def __init__(self,gamertag,platform,data={}):
		self.gamertag = gamertag
		self.platform = platform
		self.data = data or {}

	def setPlatform(self,platform):
		self.platform = platform
'''