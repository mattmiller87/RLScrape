#!/usr/bin/python3

#this file holds methods for asynccsv and synccsv and cannot be run directly

import requests
import csv
import os
import re

class rlCSV():
	'''I/O for CSV'''
	#class variables
	seasons = []
	tiertf = False
	def __init__(self,argresults):
		self._checkFolders()
		self.csvinput = argresults.input
		self.csvoutput = argresults.output
		self.seasons = argresults.seasons
		self.returndata = argresults.returndata
		self.latestseason = '13' #need a better way to update this, perhaps dynamically?
		self.header = []
		tierchoices = ['1T','2T','3ST','3T','All']
		tiermatch = [item for item in tierchoices if item in self.returndata]
		if len(tiermatch) > 0:
			self.tiertf = True
		else:
			self.tiertf = False
	
	#not in use currently
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
		'''read input CSV file. File MUST be structured either: preferred = *kwargs,Name,Link || optional = *kwargs,Link'''
		seasons = self.seasons
		with open(self.csvinput, 'r', newline='', encoding='latin-1') as csvread:
			reader = csv.reader(csvread)
			playerdict = {} # define a basic dict to pass csv information into
			i = 0
			for row in reader:
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
					playerdict[gamertag] = {} # define dict for each gamertag and values for that gamertag
					a = 0
					for item in row:  # handle kwargs
						if len(row) - a > 2:
							playerdict[gamertag][a] = item
							a += 1
					playerdict[gamertag]['platform'] = platform
					playerdict[gamertag]['name'] = name
					playerdict[gamertag]['link'] = link
					i += 1
		return playerdict

	async def writeCSV(self,newrows):
		'''write list of data to outputCSV file'''
		for season in self.seasons:
			header_dict = {
				'1': "S%s_1s_MMR" % (season), '1GP': "S%s_1s_GamesPlayed" % (season), '1T': "S%s_1s_Tier" % (season),
				'2': "S%s_2s_MMR" % (season), '2GP': "S%s_2s_GamesPlayed" % (season), '2T': "S%s_2s_Tier" % (season),
				'3S': "S%s_Solo_3s_MMR" % (season), '3SGP': "S%s_Solo_3s_GamesPlayed" % (season), '3ST': "S%s_Solo3s_Tier" % (season),
				'3': "S%s_3s_MMR" % (season), '3GP': "S%s_3s_GamesPlayed" % (season), '3T': "S%s_3s_Tier" % (season),
			}
			if "All" in self.returndata:
				self.header.extend(header_dict[k] for k in header_dict)
			else:
				self.header.extend(header_dict[k] for k in header_dict if k in self.returndata)

		with open(self.csvoutput, 'w', newline='', encoding='latin-1') as csvwrite:
			w = csv.writer(csvwrite, delimiter=',')
			w.writerow(self.header)
			for newrow in newrows:
				w.writerow(newrow)

	def dictToList(self,dictdata):
		'''Take json formatted dictionary of playerdata and create a list which is better formatted for csv
		this is specifically designed for RSC'''
		latestseason = self.latestseason
		tiertf = self.tiertf
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
			if "All" in self.returndata:
				newlist.extend([v[k] for k in v])
			else:
				newlist.extend([v[k] for k in v if k in self.returndata])
		return newlist

	def _checkFolders(self):
		if not os.path.exists("Scrapes"):
			logger.info("Creating Scrapes folder...")
			os.makedirs("Scrapes")

#tierlegend =    {1:"Bronze I", 2:"Bronze II",3:"Bronze III",4:"Silver I",5:"Silver II",6:"Silver III",
#				7:"Gold I",8:"Gold II",9:"Gold III",10:"Platinum I",11:"Platinum II",12:"Platinum III",
#				13:"Diamond I",14:"Diamond II",15:"Diamond III",16:"Champion I",17:"Champion II",18:"Champion III",19:"Grand Champion"} #futureproof

