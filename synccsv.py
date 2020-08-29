#!/usr/bin/python3

import requests
import csv
import datetime
import argparse
import os
import re
from tqdm import tqdm as pbar
import asyncio
from aioify import aioify
from setup_logging import logger
from rlscrape import Webscrape

readibletime =  datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # used for csvWrite
sem = asyncio.Semaphore(50) # control how many urls are being retrieved at a time

class csvIO:
	''' I/O for CSV
	'''
	def __init__(self):
		checkFolders()
		self.csvinput = results.input
		self.csvoutput = results.output
		self.seasons = results.seasons
		self.playlists = results.playlists
		self.latestseason = '14' # need a better way to update this, perhaps dynamically?
		self.header = []

	def readCSVLinks(self):
		''' Read input CSV file. File MUST be structured either: preferred = *kwargs,Name,Link || optional = *kwargs,Link
		'''
		seasons = self.seasons
		with open(self.csvinput, 'r', newline='', encoding='latin-1') as csvread:
			reader = csv.reader(csvread)
			playerdict = {} # define a basic dict to pass csv information into
			i = 0
			for row in reader:
				playerdict[i] = {}
				if i < 1: # define headers
					self.header = [str(i+1) for i in range(len(row))] # handle kwargs as header - assign number
					self.header[-2] = "Name"
					self.header[-1] = "Link"
				name,link = row[-2:] # select last two items
				try:
					gamertag = link.split('/')[-1] # last item in link is gamertag
					platform = link.split('/')[-2] # item before gamertag is platform
				except IndexError:
					logger.error("Gamertag:%(name)s Link:%(link)s is not formatted properly" % locals())
				else:
					playerdict[i][gamertag] = {} # define dict for each gamertag and values for that gamertag
					a = 0
					for item in row:  # handle kwargs
						if len(row) - a > 2:
							playerdict[i][gamertag][a] = item
							a += 1
					if "ps4" or "ps" in platform:
						platform = "psn"
					elif "xbox" in platform:
						platform = "xbl"
					playerdict[i][gamertag]['platform'] = platform
					playerdict[i][gamertag]['name'] = name
					playerdict[i][gamertag]['link'] = link
					i += 1
		return playerdict

	def RetrieveData(self,gamertag,gamerdict):
		platform = gamerdict['platform']
		name = gamerdict['name']
		link = gamerdict['link']
		scrape = Webscrape()
		seasons = self.seasons
		newrow = []
		data = scrape.retrieveDataRLTracker(gamertag=gamertag,platform=platform,seasons=seasons)
		newrow = self._dictToList(data)
		a = 0
		for k,v in gamerdict.items(): # handle kwargs
			if a == k:
				newrow.insert(a,v)
				a += 1
		newrow.insert(a,name)
		newrow.insert(a+1,link)
		return newrow

	def writeCSV(self,newrows):
		''' Write list of data to outputCSV file
		'''
		for season in self.seasons:
			header_dict = {
				'1': "S%s_1s_MMR" % (season), '1GP': "S%s_1s_GamesPlayed" % (season),
				'2': "S%s_2s_MMR" % (season), '2GP': "S%s_2s_GamesPlayed" % (season),
				'3S': "S%s_Solo_3s_MMR" % (season), '3SGP': "S%s_Solo_3s_GamesPlayed" % (season),
				'3': "S%s_3s_MMR" % (season), '3GP': "S%s_3s_GamesPlayed" % (season),
			}
			if "All" in self.playlists:
				self.header.extend(header_dict[k] for k in header_dict)
			else:
				self.header.extend(header_dict[k] for k in header_dict if k in self.playlists)

		with open(self.csvoutput, 'w',newline='', encoding='latin-1') as csvwrite:
			w = csv.writer(csvwrite, delimiter=',')
			w.writerow(self.header)
			for newrow in newrows:
				w.writerow(newrow)

	def _dictToList(self,dictdata):
		'''Take json formatted dictionary of playerdata and create a list which is better formatted for csv
		this is specifically designed for RSC'''
		latestseason = self.latestseason
		newdict = {}
		for gamertag,gdata in dictdata.items():
			for season,sdata in gdata.items():
				newdict[season] = {
					'1': None,  '1GP': None,
					'2': None, '2GP': None,
					'3S': None, '3SGP': None,
					'3': None, '3GP': None,
				}
				for playlist,pdata in sdata.items():
					if playlist in 'Ranked Duel 1v1' and pdata is not None and pdata.items():
						newdict[season]['1'] = pdata['MMR']
						newdict[season]['1GP'] = pdata['Games Played']
					if playlist in 'Ranked Doubles 2v2' and pdata is not None and pdata.items():
						newdict[season]['2'] = pdata['MMR']
						newdict[season]['2GP'] = pdata['Games Played']
					if playlist in 'Ranked Solo Standard 3v3' and pdata is not None and pdata.items():
						newdict[season]['3S'] = pdata['MMR']
						newdict[season]['3SGP'] = pdata['Games Played']
					if playlist in 'Ranked Standard 3v3' and pdata is not None and pdata.items():
						newdict[season]['3'] = pdata['MMR']
						newdict[season]['3GP'] = pdata['Games Played']
		newlist = []
		for season in self.seasons:
			for dictseason,v in newdict.items():
				if season == dictseason:
					if "All" in self.playlists:
						newlist.extend([v[k] for k in v])
					else:
						newlist.extend([v[k] for k in v if k in self.playlists])
		return newlist

def checkFolders():
	if not os.path.exists("Scrapes"):
		logger.info("Creating Scrapes folder...")
		os.makedirs("Scrapes")
	
def singleRun():
	logger.info("Start for csv input:%s" % (results.input))
	inputoutput = csvIO() # initialize class
	datadict = inputoutput.readCSVLinks() # read the csv file
	tasks = []
	for i,idict in datadict.items():
		for k,v in idict.items():
			task = inputoutput.RetrieveData(k,v) # start the retrieve process
			tasks.append(task)
	'''
	responses = []
	for task in pbar(tasks,desc='retrieve',total=len(tasks)):
		responses.append(task)
	inputoutput.writeCSV(responses)
	'''
	inputoutput.writeCSV(tasks)
	logger.info("Finish for csv output:%s" % (results.output))
	
if __name__ == "__main__":
	''' Run locally to this script'''
	# Use comandline arguments for input
	# edit the default parameter to change options manually without commandline options
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-i', action='store', dest='input', help='Input CSV to use', default='example.csv')
	parser.add_argument('-o', action='store', dest='output', help='Output CSV to use', default='Scrapes/%s_RLTN.csv' % (readibletime)) #RLTN = RocketLeague Tracker Network
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
	parser.add_argument('-p', action='store', dest='playlists', help='playlist options. Example: 1 2 3S 3', choices=("1","2","3S","3","1GP","2GP","3SGP","3GP","All"), nargs='+', default="['1','1GP','2','2GP','3S','3SGP','3','3GP']")
	
	results = parser.parse_args()
	#tierlegend =    {1:"Bronze I", 2:"Bronze II",3:"Bronze III",4:"Silver I",5:"Silver II",6:"Silver III",
	#				7:"Gold I",8:"Gold II",9:"Gold III",10:"Platinum I",11:"Platinum II",12:"Platinum III",
	#				13:"Diamond I",14:"Diamond II",15:"Diamond III",16:"Champion I",17:"Champion II",18:"Champion III",19:"Grand Champion"} #futureproof
	
	singleRun()
