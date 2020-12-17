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
    '''I/O for CSV'''
    def __init__(self):
        checkFolders()
        self.csvinput = results.input
        self.csvoutput = results.output
        # self.seasons = results.seasons
        self.playlists = results.playlists
        self.latestseason = '16' #need a better way to update this, perhaps dynamically?
        self.header = []
        tierchoices = ['1T','2T','TournamentT','3T','All']
        tiermatch = [item for item in tierchoices if item in self.playlists]
        if len(tiermatch) > 0:
            self.tiertf = True
        else:
            self.tiertf = False

    def areadCSVLinks(self):
        '''read input CSV file. File MUST be structured either: preferred = *kwargs,Name,Link || optional = *kwargs,Link'''
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
                    playerdict[i][gamertag]['platform'] = platform
                    playerdict[i][gamertag]['name'] = name
                    playerdict[i][gamertag]['link'] = link
                    i += 1
        return playerdict

    async def aRetrieveData(self,gamertag,gamerdict):
        platform = gamerdict['platform']
        name = gamerdict['name']
        link = gamerdict['link']
        scrape = Webscrape()
        newrow = []
        aioretrieve = aioify(obj=scrape.retrieveDataRLTracker, name='aioretrieve')
        data = await aioretrieve(gamertag=gamertag,platform=platform)
        newrow = self._dictToList(data)
        a = 0
        for k,v in gamerdict.items(): # handle kwargs
            if a == k:
                newrow.insert(a,v)
                a += 1
        newrow.insert(a,name)
        newrow.insert(a+1,link)
        return newrow

    def awriteCSV(self,newrows):
        '''write list of data to outputCSV file'''
        season = self.latestseason
        header_dict = {
            '1': "S%s_1s_MMR" % (season), '1GP': "S%s_1s_GamesPlayed" % (season), '1T': "S%s_1s_Tier" % (season),
            '2': "S%s_2s_MMR" % (season), '2GP': "S%s_2s_GamesPlayed" % (season), '2T': "S%s_2s_Tier" % (season),
            'Tournament': "S%s_Tournament_MMR" % (season), 'TournamentGP': "S%s_Tournament_GamesPlayed" % (season), '3ST': "S%s_Solo3s_Tier" % (season),
            '3': "S%s_3s_MMR" % (season), '3GP': "S%s_3s_GamesPlayed" % (season), '3T': "S%s_3s_Tier" % (season),
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
        tiertf = self.tiertf
        newdict = {}
        for gamertag,gdata in dictdata.items():
            for season,sdata in gdata.items():
                newdict[season] = {
                    '1': None,  '1GP': None, '1T' : None,
                    '2': None, '2GP': None,  '2T' : None,
                    'Tournament': None, 'TournamentGP': None, 'TournamentT' : None, 
                    '3': None, '3GP': None, '3T' : None
                }
                for playlist,pdata in sdata.items():
                    if playlist in 'Ranked Duel 1v1' and pdata is not None and pdata.items():
                        newdict[season]['1'] = pdata['MMR']
                        newdict[season]['1GP'] = pdata['Games Played']
                        if tiertf:
                            newdict[season]['1T'] = pdata['Tier Number']
                    if playlist in 'Ranked Doubles 2v2' and pdata is not None and pdata.items():
                        newdict[season]['2'] = pdata['MMR']
                        newdict[season]['2GP'] = pdata['Games Played']
                        if tiertf:
                            newdict[season]['2T'] = pdata['Tier Number']
                    if playlist in 'Tournament' and pdata is not None and pdata.items():
                        newdict[season]['Tournament'] = pdata['MMR']
                        newdict[season]['TournamentGP'] = pdata['Games Played']
                        if tiertf:
                            newdict[season]['TournamentT'] = pdata['Tier Number']
                    if playlist in 'Ranked Standard 3v3' and pdata is not None and pdata.items():
                        newdict[season]['3'] = pdata['MMR']
                        newdict[season]['3GP'] = pdata['Games Played']
                        if tiertf:
                            newdict[season]['3T'] = pdata['Tier Number']
        newlist = []
        for dictseason,v in newdict.items():
            if "All" in self.playlists:
                newlist.extend([v[k] for k in v])
            else:
                newlist.extend([v[k] for k in v if k in self.playlists])
        return newlist
    
    async def _safe_download(self,gamertag,platform):
        async with sem: # only allow so many retrieve requests at a time - helps with progress bar too
            return await self.aRetrieveData(gamertag,platform)

def checkFolders():
    if not os.path.exists("Scrapes"):
        logger.info("Creating Scrapes folder...")
        os.makedirs("Scrapes")
    
async def singleRun():
    logger.info("Start for csv input:%s" % (results.input))
    inputoutput = csvIO() # initialize class
    datadict = inputoutput.areadCSVLinks() # read the csv file
    tasks = []
    for i,idict in datadict.items():
        for k,v in idict.items():
            task = loop.create_task(inputoutput._safe_download(k,v)) # start the retrieve process
            tasks.append(task)
    responses = []
    for task in pbar(asyncio.as_completed(tasks),desc='retrieve',total=len(tasks)):
        responses.append(await task)
    inputoutput.awriteCSV(responses)
    logger.info("Finish for csv output:%s" % (results.output))

if __name__ == "__main__":
    '''Run locally to this script'''
    #Use comandline arguments for input
    #edit the default parameter to change options manually without commandline options
    parser = argparse.ArgumentParser(description='Scrape Commandline Options', add_help=True)
    parser.add_argument('-i', action='store', dest='input', help='Input CSV to use', default='example.csv')
    parser.add_argument('-o', action='store', dest='output', help='Output CSV to use', default='Scrapes/%s_RLTN.csv' % (readibletime)) #RLTN = RocketLeague Tracker Network
    ###
    # no longer can search for multiple seasons - this may be revisited at some point
    #parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
    ##
    parser.add_argument('-p', action='store', dest='playlists', help='playlist options. Example: 1 2 3S 3', choices=("1","2","Tournament","3","1GP","2GP","TournamentGP","3GP","1T","2T","TournamentT","3T","All"), nargs='+', default="['1','1GP','2','2GP','Tournament','TournamentGP','3','3GP']")
    
    results = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(singleRun())
    loop.close()