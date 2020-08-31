#!/usr/bin/python3

# from bs4 import BeautifulSoup
import argparse
import requests
import re
from setup_logging import logger

class APIget():
	''' 	https://api.tracker.gg/api/v2/rocket-league/standard/profile/
	'''
	def __init__(self):
		self.apiurl = "https://api.tracker.gg/api/v2/rocket-league/standard/profile/"

	def pull(self,gamertag="memlo",platform="steam",seasons=["14"]):
		'''
		data.segments
		0 = lifetime
		1 = Unranked
		2 = Ranked Duel 1v1
		3 = Ranked Doubles 2v2
		4 = Ranked Solo Standard 3v3
		5 = Ranked Standard 3v3
		.attributes: season:
		.metadata: name: # playlist
		.stats:
			.tier: metadata: name: # Rank in text form
			.matchesPlayed: value: # gamesplayed
			.rating: value: # mmr
		'''
		apiurl = self.apiurl
		playerurl = "%(apiurl)s%(platform)s/%(gamertag)s" % locals()
		if '[]' in seasons:
			logger.critical("Season was not set - you should never see this error")
		data = requests.get(playerurl).json()

		playerdata = {} # define the player dict
		playerdata[gamertag] = {} # define the gamertag dict
		# try to load the data
		try:
			fulldata = data["data"]
		except Exception as e:
			# generic exception handler
			logger.error("Gamertag:%(gamertag)s, platform: %(platform)s for url: %(playerurl)s data was not found." % locals())
		else:
			for season in seasons:
					playerdata[gamertag][season] = {} # define the season dict
					for playlistdata in data["data"]["segments"]:
						if "playlist" in playlistdata["type"]:
							playlist = playlistdata["metadata"]["name"]
							playerdata[gamertag][season][playlist] = {} # define the playlist dict
							mmr = playlistdata["stats"]["rating"]["value"]
							gp = playlistdata["stats"]["matchesPlayed"]["value"]
							rank = playlistdata["stats"]["tier"]["metadata"]["name"]
							playerdata[gamertag][season][playlist]["MMR"] = mmr
							playerdata[gamertag][season][playlist]["Games Played"] = gp
							playerdata[gamertag][season][playlist]["Rank"] = rank
		return(playerdata)

def _singleRun(gamertag,platform,seasons):
	apiget = APIget()
	data = apiget.pull(gamertag=gamertag,platform=platform,seasons=seasons)
	pprint(data)

if __name__ == "__main__":
	'''Run locally to this script'''

	from pprint import pprint # pprint is cool
	#Pass arguments for name and platform
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-p', action='store', dest='platform', help='platform options. Example: steam', choices=('steam','psn','xbl'), default='steam')
	parser.add_argument('-g', action='store', dest='gamertag', help='your gamertag', default='memlo')
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
	
	results = parser.parse_args()
	platform = results.platform
	gamertag = results.gamertag
	seasons = results.seasons
	
	_singleRun(gamertag,platform,seasons)
