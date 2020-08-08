#!/usr/bin/python3

from bs4 import BeautifulSoup
import argparse
import requests
import re
from setup_logging import logger
import aiohttp
import asyncio


class Webscrape():
	'''classes are cool, no other real reason to use this - probably going to only have one function'''
	def __init__(self):
		self.webpath = "https://rocketleague-beta.tracker.network/rocket-league/profile"
		#				https://rocketleague-beta.tracker.network/rocket-league/profile/steam/76561198049122040/overview
		# self.webpath = "https://rocketleague.tracker.network/profile"
		self.webpathmmr = "https://rocketleague.tracker.network/profile/mmr"
		self.latestseason = '14' #need a better way to update this, perhaps dynamically?
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
			logger.critical("Season was not set - you should never see this error")
		page = requests.get("%(webpath)s/%(platform)s/%(gamertag)s" % locals())
		if page.status_code == 200:
			soup = BeautifulSoup(page.content, features="lxml")
			if soup(text=re.compile(rltrackermissing)): # find "we could not find your stats" on webpage
				logger.critical("Player Missing - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
			elif soup(text=re.compile(psyonixdisabled)): # find "Psyonix has disabled the Rocket League API" on webpage
				logger.critical("Psyonix Disabled API - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
			else:
				if '[]' not in seasons:
					for season in seasons:
						if self._testSeason(season):
							playerdata[gamertag][season] = {} #define the season dict
							seasonid = "season-%(season)s" % locals()
							try:
								newseasontable = soup.find('div', id=seasonid).select('table > tbody', class_="card-table items")[-1].select('tr')
							except:
								logger.error("Finding season:%(season)s data for gamertag:%(gamertag)s" % locals())
							else:
								for newtabledata in newseasontable:
									listdata = []
									td = newtabledata.find_all('td')[1:]
									for i,x in enumerate(td):
										if i == 0:
											playlist = x.text.strip().split('\n')[0]
											listdata.append(playlist)
										else:
											data = (x.text.strip().split('\n'))[0]
											listdata.append(data)
									if int(season) == int(latestseason):
										playlist,divdown,mmr,divup,gamesplayed = listdata
										if mmr == "n/a":
											mmr = 0
										if gamesplayed == "n/a":
											gamesplayed = 0
										if type(mmr) == str:
											mmr = int(mmr.replace(",",""))
										if type(gamesplayed) == str:
											gamesplayed = int(gamesplayed.replace(",",""))
									else:
										playlist,mmr,gamesplayed = listdata
									playerdata[gamertag][season][playlist] = {} # define the playlist dict
									playerdata[gamertag][season][playlist]['MMR'] = mmr
									playerdata[gamertag][season][playlist]['Games Played'] = gamesplayed
				if tiertf == True:
					if latestseason in seasons:
						pagemmr = requests.get("%(webpathmmr)s/%(platform)s/%(gamertag)s" % locals())
						if pagemmr.status_code == 200:
							soupmmr = BeautifulSoup(pagemmr.content, features="lxml")
							try:
								scripttags = soupmmr.findAll('script', type='text/javascript') #grab all <script> tags
							except:
								logger.error("Finding <script> tags in website:%(webpathmmr)s/%(platform)s/%(gamertag)s" % locals())
							else:
								scripttags = soupmmr.findAll('script', type='text/javascript') #grab all <script> tags
								for script in scripttags: #find the data we care about
									if 'var data' in script.text:
										a = script.text.replace(' ','').replace('\n','').replace('\r','').split(';') 
										data = {}
										for blob in a[1:6]:
											b = re.split('\w+.:',blob)
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
											try:
												playerdata[gamertag][latestseason][playlist]
											except:
												playerdata[gamertag][latestseason][playlist] = {}
											else:
												if '[]' in b[2]:
													playerdata[gamertag][latestseason][playlist]['Tier'] = None
												else:
													#dates = list(filter(None, re.split('\[|,|\]|\'',b[2]))) #futureproof
													#rating_over_time' = list(filter(None, re.split('\[|,|\]',b[3]))) #futureproof
													tier_over_time = list(filter(None, re.split('\[|,|\]|\}',b[4])))
													if tier_over_time is not None:
														playerdata[gamertag][latestseason][playlist]['Tier'] = tier_over_time[-1]
													else:
														playerdata[gamertag][latestseason][playlist]['Tier'] = None
		if '{}' in playerdata[gamertag]: #condition to alert if gamertag retrieval was blank
			logger.debug("Gamertag: %(gamertag)s had no data to retrieve" % locals())
		logger.debug("Data retrieval complete for gamertag: %(gamertag)s" % locals()) # a simple measure to make sure we catch every player when a list is ran
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

	async def fetch(self, session, url):
		async with session.get(url) as response:
			return await response.text()

	async def retrieveDataRLTracker_beta(self,gamertag="memlo",platform="steam",seasons=["12"],tiertf=False):
		'''RLTracker is updating to a beta website with javascript loading the player data'''
		latestseason = self.latestseason
		webpathmmr = self.webpathmmr
		webpath = self.webpath
		rltrackermissing = self.rltrackermissing
		psyonixdisabled = self.psyonixdisabled
		playerdata = {} # define the playerdata dict
		playerdata[gamertag] = {} # define the gamertag dict
		if '[]' in seasons:
			logger.critical("Season was not set - you should never see this error")
		page = requests.get("%(webpath)s/%(platform)s/%(gamertag)s" % locals())
		if page.status_code == 200:
			async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10,ssl=False)) as session:
			#async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
				url = ("%(webpath)s/%(platform)s/%(gamertag)s" % locals())
				html = await self.fetch(session, "https://rocketleague-beta.tracker.network/rocket-league/profile/steam/76561198049122040")
				soup = BeautifulSoup(html, "lxml")
				title = soup.find('title')
				print(soup)

async def _singleRun(gamertag,platform,seasons):
	'''Single run of Webscrape.retrieveDataRLTracker'''
	logger.info("Start for gamertag:%(gamertag)s"% locals())
	scrape = Webscrape()
	data = await scrape.retrieveDataRLTracker_beta(gamertag=gamertag,platform=platform,seasons=seasons,tiertf=True)
	if data is not None:
		pprint(data)
		logger.info("Finish for gamertag:%(gamertag)s"% locals())

if __name__ == "__main__":
	'''Run locally to this script'''

	from pprint import pprint # pprint is cool
	#Pass arguments for name and platform
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-p', action='store', dest='platform', help='platform options. Example: steam', choices=('steam','ps4','xbox'), default='steam')
	parser.add_argument('-g', action='store', dest='gamertag', help='your gamertag', default='memlo')
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
	
	results = parser.parse_args()
	platform = results.platform
	gamertag = results.gamertag
	seasons = results.seasons
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(_singleRun(gamertag,platform,seasons))
	loop.close()

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