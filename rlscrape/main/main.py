#!/usr/bin/python3

from bs4 import BeautifulSoup
import argparse
import requests
import re
import os
import logging

class Log():
	'''create logger which can be used anywhere'''
	logger = None
	def run(self,logfolder="logs"):
		#Set up logging
		if not os.path.exists(logfolder):
			os.makedirs(logfolder)
		if None == self.logger:
			self.logger = logging.getLogger('appLog')
			self.logger.setLevel(logging.INFO)
			handler = logging.FileHandler(filename = "%(logfolder)sscrape.log" % locals())
			fmt = '%(levelname)s - %(asctime)s - %(funcName)s: %(message)s'
			datefmt = '%Y-%m-%d %H:%M:%S'
			formatter = logging.Formatter(fmt,datefmt)
			handler.setFormatter(formatter)
			self.logger.addHandler(handler)
		return self.logger

class Webscrape():
	'''classes are cool, no other real reason to use this - probably going to only have one function'''
	logger = Log().run(logfolder="../logs")
	def __init__(self):
		self.webpath = "https://rocketleague.tracker.network/profile"
		self.webpathmmr = "https://rocketleague.tracker.network/profile/mmr"
		self.latestseason = '13' #need a better way to update this, perhaps dynamically?
		self.rltrackermissing = "We could not find your stats,"
		self.psyonixdisabled = "Psyonix has disabled the Rocket League API"

	def retrieveDataRLTracker(self,gamertag="memlo",platform="steam",seasons=["12"],tiertf=False):
		'''Python BeautifulSoup4 Webscraper to https://rocketleague.tracker.network/ to retrieve gamer data'''
		playlistdict = {0:'Un-Ranked',10:'Ranked Duel 1v1', 11:'Ranked Doubles 2v2',
				12:'Ranked Solo Standard 3v3',13:'Ranked Standard 3v3',
				27:'Hoops',28:'Rumble',29:'Dropshot',30:'Snowday'} 
		latestseason = self.latestseason
		webpathmmr = self.webpathmmr
		webpath = self.webpath
		rltrackermissing = self.rltrackermissing
		psyonixdisabled = self.psyonixdisabled
		playerdata = {} # define the playerdata dict
		playerdata[gamertag] = {} # define the gamertag dict
		if '[]' in seasons:
			self.logger.warning("Season was not set - you should never see this error")
		page = requests.get("%(webpath)s/%(platform)s/%(gamertag)s" % locals())
		if page.status_code == 200:
			soup = BeautifulSoup(page.content, features="lxml")
			if soup(text=re.compile(rltrackermissing)): # find "we could not find your stats" on webpage
				self.logger.critical("Player Missing - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
			elif soup(text=re.compile(psyonixdisabled)): # find "Psyonix has disabled the Rocket League API" on webpage
				self.logger.critical("Psyonix Disabled API - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
			else:
				if latestseason in seasons:
					playerdata[gamertag][latestseason] = {} #define the season dict
					pagemmr = requests.get("%(webpathmmr)s/%(platform)s/%(gamertag)s" % locals())
					if pagemmr.status_code == 200:
						soupmmr = BeautifulSoup(pagemmr.content, features="lxml")
						# for every playlist, create a record of data
						# on the website, grab the 'div' for specific playlist
						for numrank,playlist in playlistdict.items():
							try:
								soupmmr.find('a',{"data-id": numrank }).find('span').text
							except:
								playerdata[gamertag][latestseason][playlist] = None
							else:
								playerdata[gamertag][latestseason][playlist] = {} #define the playlist dict
								playerdata[gamertag][latestseason][playlist]['MMR'] = soupmmr.find('a',{"data-id": numrank }).find('span').text
								playerdata[gamertag][latestseason][playlist]['Games Played'] = soupmmr.find('div',{"data-id": numrank }).find('div').find('span').text
								playerdata[gamertag][latestseason][playlist]['Rank'] = soupmmr.find('div',{"data-id": numrank }).select('div > span')[2].text  
								playerdata[gamertag][latestseason][playlist]['Rank Division'] = soupmmr.find('div',{"data-id": numrank }).select('div > h4')[2].text
						if tiertf == True:
							try:
								scripttags = soupmmr.findAll('script', type='text/javascript') #grab all <script> tags
							except:
								self.logger.error("Finding <script/> tags in website:%(webpathmmr)s/%(platform)s/%(gamertag)s" % locals())
							else:
								scripttags = soupmmr.findAll('script', type='text/javascript') #grab all <script> tags
								for script in scripttags: #find the data we care about
									if 'var data' in script.text:
										a = script.text.replace(' ','').replace('\n','').replace('\r','').split(';') 
										data = {}
										for blob in a[1:6]:
											b = re.split('\w+.:',blob)
											if '[]' in b[2] and 'Un-Ranked' not in b[2]: #if there aren't any dates listed, except in Un-Ranked
												#logger.error("Issue for player:%s in season:%s with dates:%s and tier:%s in playlist:%s" % (gamertag,latestseason,b[2],b[4],b[1])) # this logs a ton
												continue
											else:
												if 'Un-Ranked' in b[1]:
													playlist = 'Un-Ranked'
												elif 'RankedDuel1v1' in b[1]:
													playlist = 'Ranked Duel 1v1'
												elif 'RankedDoubles2v2' in b[1]:
													playlist = 'Ranked Doubles 2v2'
												elif 'RankedSoloStandard3v3' in b[1]:
													playlist = 'Ranked Solo Standard 3v3'
												elif 'RankedStandard3v3' in b[1]:
													playlist = 'Ranked Standard 3v3'
												else:
													playlist = ''
												#dates = list(filter(None, re.split('\[|,|\]|\'',b[2]))) #futureproof
												#rating_over_time' = list(filter(None, re.split('\[|,|\]',b[3]))) #futureproof
												tier_over_time = list(filter(None, re.split('\[|,|\]|\}',b[4])))
												if tier_over_time is not None:
													playerdata[gamertag][latestseason][playlist]['Tier'] = tier_over_time[-1]
												else:
													playerdata[gamertag][latestseason][playlist]['Tier'] = None
				if '[]' not in seasons:
					for season in seasons:
						if self._testSeason(season):
							playerdata[gamertag][season] = {} #define the season dict
							seasonid = "season-%(season)s" % locals()
							try:
								seasontable = soup.find(id=seasonid).select('table > tbody')[0].select('tr')[1:]
							except:
								#self.logger.error("Finding season:%(season)s data for gamertag:%(gamertag)s" % locals()) # this can log a lot
								continue
							else:
								seasontable = soup.find(id=seasonid).select('table > tbody')[0].select('tr')
								playerdata[gamertag][season] #define the playlist dict
								for tabledata in seasontable:
									td = tabledata.find_all('td')
									listdata = []
									for x in td:
										data = x.text.strip().split('\n')
										listdata = listdata+data
									try:
										blank1,playlist,blank2,writtenrank,mmr,gamesplayed = listdata
									except ValueError:
										self.logger.error("Error parsing:%(listdata)s season:%(season)s data for gamertag:%(gamertag)s" % locals())
									else:
										blank1,playlist,blank2,writtenrank,mmr,gamesplayed = listdata
										playerdata[gamertag][season][playlist] = {} #define the playlist dict
										playerdata[gamertag][season][playlist]['MMR'] = mmr
										playerdata[gamertag][season][playlist]['Games Played'] = gamesplayed
		return playerdata

	def _testSeason(self,season):
		'''True/False to see if season is valid
		1) is a number, 2) is a valid season less than current number, 3) if current season in list, just pass'''
		latestseason = self.latestseason
		try:
			if not season.isdigit():
				raise NameError
			if int(season) > int(latestseason):
				raise ValueError
			if int(season) == int(latestseason):
				return False
		except ValueError:
			self.logger.error("Season:%(season)s was higher than Current Season:%(latestseason)s" % locals())
			return False
		except NameError:
			self.logger.error("Season:%(season)s was not a number" % locals())
			return False
		else:
			return True

				
def singleRun(gamertag,platform,seasons):
	'''Single run of Webscrape.retrieveDataRLTracker'''
	#define logging behavior
	logger.info("Start for gamertag:%(gamertag)s" % locals())
	#run scrape
	data = Webscrape().retrieveDataRLTracker(gamertag=gamertag,platform=platform,seasons=seasons,tiertf=True)
	if data is not None:
		pprint(data)
		logger.info("Finish for gamertag:%(gamertag)s" % locals())
	else:
		logger.warning("Unexpected no data found for gamertag:%(gamertag)s" % locals())

if __name__ == "__main__":
	'''Run locally to this script'''
	from pprint import pprint # pprint is cool

	#Pass arguments for name and platform
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-p', action='store', dest='platform', help='platform options. Example: steam', choices=('steam','ps','xbox'), default='steam')
	parser.add_argument('-g', action='store', dest='gamertag', help='your gamertag', default='memlo')
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['13']) #need a better way to update this, perhaps dynamically?
	
	results = parser.parse_args()
	platform = results.platform
	gamertag = results.gamertag
	seasons = results.seasons
	logger = Log().run("../logs")
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