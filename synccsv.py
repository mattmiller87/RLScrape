#!/usr/bin/python3

import requests
import csv
import datetime
import argparse
import os
import re
from tqdm import tqdm
from setup_logging import logger
from rlscrape import Webscrape

#instance = Webscrape() # instantiate the module before running it
readibletime =  datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

class csvIO:
	'''I/O for CSV'''
	def __init__(self):
		checkFolders()
		self.csvinput = results.input
		self.csvoutput = results.output
		self.seasons = results.seasons
		self.playlists = results.playlists
		self.latestseason = '13' #need a better way to update this, perhaps dynamically?
		self.header = []
		self.rows = []
		self.newrows = []
		tierchoices = ['1T','2T','3ST','3T','All']
		tiermatch = [item for item in tierchoices if item in self.playlists]
		if len(tiermatch) > 0:
			self.tiertf = True
		else:
			self.tiertf = False

	def readCSVGamertagPlatform(self):
		'''read input CSV file.  File MUST be structured either: Gamertag,Platform || *kwargs,Gamertag,Platform'''
		with open(self.csvinput, 'r', newline='', encoding='latin-1') as csvread:
			reader = csv.reader(csvread)
			i = 0
			for row in reader:
				if i < 1:
					self.header = [str(i+1) for i in range(len(row))]  #account for kwargs
					self.header[-2] = "Gamertag"
					self.header[-1] = "Platform"
					self.rows.append(row)
					i += 1
				else:
					self.rows.append(row)
					i += 1
		self._parseRowstoData()
		return self.newrows

	def readCSVLinks(self):
		'''read input CSV file. File MUST be structured either: Link || *kwargs,Link || *kwargs,Name,Link'''
		scrape = Webscrape()
		seasons = self.seasons

		with open(self.csvinput, newline ='', encoding="ISO-8859-1") as csvread:
			reader = csv.reader(csvread)
			i = 0
			for row in reader:
				if i < 1:
					self.header = [str(i+1) for i in range(len(row))]
					self.header[-2] = "ID"
					self.header[-1] = "Link"
					self.rows.append(row)
					i += 1
				else:
					self.rows.append(row)
					i += 1
		row_count = sum(1 for row in self.rows)
		i = 1
		for row in tqdm(self.rows, total=row_count):
			name,link = row[-2:] # select last two items
			try:
				gamertag = link.split('/')[-1] # last item in link is gamertag
				platform = link.split('/')[-2] # item before gamertag is platform
			except IndexError:
				logger.error("Gamertag:%(name)s Link:%(link)s is not formatted properly" % locals())
				i += 1
			else:
				newrow = []
				data = scrape.retrieveDataRLTracker(gamertag=gamertag,platform=platform,seasons=seasons,tiertf=self.tiertf)
				newrow = self._dictToList(data)
				a = 0
				for item in row: #account for kwargs
					newrow.insert(a,item)
					a += 1
				self.newrows.append(newrow)
				i += 1
		self.writeCSV()

	def writeCSV(self):
		'''write list of data to outputCSV file'''
		for season in self.seasons:
			header_dict = {
				'1': "S%s_1s_MMR" % (season), '1GP': "S%s_1s_GamesPlayed" % (season), '1T': "S%s_1s_Tier" % (season),
				'2': "S%s_2s_MMR" % (season), '2GP': "S%s_2s_GamesPlayed" % (season), '2T': "S%s_2s_Tier" % (season),
				'3S': "S%s_Solo_3s_MMR" % (season), '3SGP': "S%s_Solo_3s_GamesPlayed" % (season), '3ST': "S%s_Solo3s_Tier" % (season),
				'3': "S%s_3s_MMR" % (season), '3GP': "S%s_3s_GamesPlayed" % (season), '3T': "S%s_3s_Tier" % (season),
			}
			if "All" in self.playlists:
				self.header.extend(header_dict[k] for k in header_dict)
			else:
				self.header.extend(header_dict[k] for k in header_dict if k in self.playlists)

		with open(self.csvoutput, 'w', encoding='latin-1') as csvwrite:
			w = csv.writer(csvwrite, delimiter=',')
			w.writerow(self.header)
			for newrow in self.newrows:
				w.writerow(newrow)

	def _dictToList(self,dictdata):
		'''Take json formatted dictionary of playerdata and create a list which is better formatted for csv
		this is specifically designed for RSC'''
		latestseason = self.latestseason
		tiertf= self.tiertf

		newdict = {}
		for gamertag,gdata in dictdata.items():
			for season,sdata in gdata.items():
				newdict[season] = {
					'1': None,  '1GP': None, '1T' : None,
					'2': None, '2GP': None,  '2T' : None,
					'3S': None, '3SGP': None, '3ST' : None, 
					'3': None, '3GP': None, '3T' : None
				}
				for playlist,pdata in sdata.items():
					if playlist in 'Ranked Duel 1v1' and pdata is not None and pdata.items():
						newdict[season]['1'] = pdata['MMR']
						newdict[season]['1GP'] = pdata['Games Played']
						if (int(latestseason) == int(season)) and tiertf:
							newdict[season]['1T'] = pdata['Tier']
					if playlist in 'Ranked Doubles 2v2' and pdata is not None  and pdata.items():
						newdict[season]['2'] = pdata['MMR']
						newdict[season]['2GP'] = pdata['Games Played']
						if (int(latestseason) == int(season)) and tiertf:
							newdict[season]['2T'] = pdata['Tier']
					if playlist in 'Ranked Solo Standard 3v3' and pdata is not None  and pdata.items():
						newdict[season]['3S'] = pdata['MMR']
						newdict[season]['3SGP'] = pdata['Games Played']
						if (int(latestseason) == int(season)) and tiertf:
							newdict[season]['3ST'] = pdata['Tier']
					if playlist in 'Ranked Standard 3v3' and pdata is not None  and pdata.items():
						newdict[season]['3'] = pdata['MMR']
						newdict[season]['3GP'] = pdata['Games Played']
						if (int(latestseason) == int(season)) and tiertf:
							newdict[season]['3T'] = pdata['Tier']
	
		newlist = []
		for season,v in newdict.items():
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
	logger.info("Start for csv input:%s"% (results.input))
	csvIO().readCSVLinks()
	logger.info("Finish for csv output:%s"% (results.output))

if __name__ == "__main__":
	'''Run locally to this script'''

	from pprint import pprint

	#Use comandline arguments for input
	#edit the default parameter to change options manually without commandline options
	parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
	parser.add_argument('-i', action='store', dest='input', help='Input CSV to use', default='example.csv')
	parser.add_argument('-o', action='store', dest='output', help='Output CSV to use', default='Scrapes/%s_RLTN.csv' % (readibletime)) #RLTN = RocketLeague Tracker Network
	parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['13']) #need a better way to update this, perhaps dynamically?
	parser.add_argument('-p', action='store', dest='playlists', help='playlist options. Example: 1 2 3S 3', choices=("1","2","3S","3","1GP","2GP","3SGP","3GP","1T","2T","3ST","3T","All"), nargs='+', default="All")
	
	results = parser.parse_args()
	#tierlegend =    {1:"Bronze I", 2:"Bronze II",3:"Bronze III",4:"Silver I",5:"Silver II",6:"Silver III",
	#				7:"Gold I",8:"Gold II",9:"Gold III",10:"Platinum I",11:"Platinum II",12:"Platinum III",
	#				13:"Diamond I",14:"Diamond II",15:"Diamond III",16:"Champion I",17:"Champion II",18:"Champion III",19:"Grand Champion"} #futureproof
	
	singleRun()
