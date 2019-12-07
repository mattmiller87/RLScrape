#!/usr/bin/python3

import requests
import datetime
import argparse
from tqdm import tqdm as pbar
from main.main import Log,Webscrape
from csvio.maincsv import rlCSV

logger = Log().run(logfolder="logs")
scrape = Webscrape()

readibletime =  datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

class synccsv:
	'''utilize a couple sync functions'''
	def retrieveData(self,gamertag,gamerdict):
		platform = gamerdict['platform']
		name = gamerdict['name']
		link = gamerdict['link']
		seasons = csvIO.seasons
		tiertf = csvIO.tiertf
		newrow = []
		data = scrape.retrieveDataRLTracker(gamertag=gamertag,platform=platform,seasons=seasons,tiertf=tiertf)
		newrow = csvIO.dictToList(data)
		a = 0
		for k,v in gamerdict.items(): # handle kwargs
			if a == k:
				newrow.insert(a,v)
				a += 1
		newrow.insert(a,name)
		newrow.insert(a+1,link)
		return newrow

def singleRun():
	logger.info("Start for csv input:%s"% (results.input))
	pdict = csvIO.readCSVLinks() # read the csv file
	for k,v in pbar(pdict.items(),desc='retrieve',total=len(pdict.items())):
		synccsv().retrieveData(k,v)
	logger.info("Finish for csv output:%s"% (results.output))

if __name__ == "__main__":
	'''Run locally to this script'''
	#Use comandline arguments for input
	#edit the default parameter to change options manually without commandline options
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-i', action='store', dest='input', help='Input CSV to use', default='example.csv')
	parser.add_argument('-o', action='store', dest='output', help='Output CSV to use', default='Scrapes/%s_RLTN.csv' % (readibletime)) #RLTN = RocketLeague Tracker Network
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['13']) #need a better way to update this, perhaps dynamically?
	parser.add_argument('-r', action='store', dest='returndata', help='data options - playlists, games played, tier. Example: 1 2 3S 3', choices=("1","2","3S","3","1GP","2GP","3SGP","3GP","1T","2T","3ST","3T","All"), nargs='+', default="All")
	results = parser.parse_args()
	csvIO = rlCSV(results) # initialize class
	
	singleRun()