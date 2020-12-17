#!/usr/bin/python3

from bs4 import BeautifulSoup
import argparse
import requests
import re
from setup_logging import logger
import json

class Webscrape():
    '''classes are cool, no other real reason to use this - probably going to only have one function'''
    def __init__(self):
        self.webpath = "https://rocketleague.tracker.network/profile"
        self.webpathmmr = "https://rocketleague.tracker.network/profile/mmr"
        self.latestseason = '16' #need a better way to update this, perhaps dynamically?
        self.rltrackermissing = "We could not find your stats,"
        self.psyonixdisabled = "Psyonix has disabled the Rocket League API"

    def retrieveDataRLTracker(self,gamertag="memlo",platform="steam"):
        ''' Python BeautifulSoup4 Webscraper to https://rocketleague.tracker.network/ to retrieve gamer data
        '''
        latestseason = self.latestseason
        webpathmmr = self.webpathmmr
        webpath = self.webpath
        rltrackermissing = self.rltrackermissing
        psyonixdisabled = self.psyonixdisabled
        playerdata = {} # define the playerdata dict
        playerdata[gamertag] = {} # define the gamertag dict
        playerdata[gamertag][latestseason] = {} # define the latestseason dict
        page = requests.get("%(webpath)s/%(platform)s/%(gamertag)s" % locals())
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, features="lxml")
            if soup(text=re.compile(rltrackermissing)): # find "we could not find your stats" on webpage
                logger.critical("Player Missing - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
            elif soup(text=re.compile(psyonixdisabled)): # find "Psyonix has disabled the Rocket League API" on webpage
                logger.critical("Psyonix Disabled API - URL:%(webpath)s/%(platform)s/%(gamertag)s" % locals())
            else:
                script_data = [l for l in [str(l.parent) for l in soup.find_all('script')] if 'INITIAL_STATE' in l][0]
                json_data = script_data.split('INITIAL_STATE__=')[1].split(";(function()")[0]
                data = json.loads(json_data)
                gamer_data = data['stats-v2']['standardProfiles']['rocket-league|%(platform)s|%(gamertag)s' % locals()]['segments']
                for segment in gamer_data:
                    if "playlist" in segment['type']:
                        playerdata[gamertag][latestseason].update(self._parsePlaylist(data=segment))
        return playerdata

    def _parsePlaylist(self,data=None):
        ''' Using the json data to assign values to the proper fields
        '''
        a = {}
        playlist = data['metadata']['name']
        a[playlist] = {"Tier Rank": None,
                       "Tier Number": None,
                       "Tier Division": None,
                       "Games Played": None,
                       "MMR": None}
        try:
            a[playlist]["Tier Rank"] = data['stats']['tier']['metadata']['name']
            a[playlist]["Tier Number"] = data['stats']['tier']['value']
            a[playlist]["Tier Divisio"] = data['stats']['division']['metadata']['name']
            a[playlist]["Games Played"] = data['stats']['matchesPlayed']['value']
            a[playlist]["MMR"] = data['stats']['rating']['value']
        except Exception as e:
            logger.info("Could not find %(playlist)s data with error: " % locals(),e)

        return a

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
                    
def singleRun(gamertag,platform):
    '''Single run of Webscrape.retrieveDataRLTracker'''
    logger.info("Start for gamertag:%(gamertag)s"% locals())
    scrape = Webscrape()
    data = scrape.retrieveDataRLTracker(gamertag=gamertag,platform=platform)
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
    ###
    # no longer can search for multiple seasons - this may be revisited at some point
    # parser.add_argument('-s', action='store', dest='seasons', help='retrieve for season(s) defined. Example: 8 9 11', nargs='+', default=['14']) #need a better way to update this, perhaps dynamically?
    ###

    results = parser.parse_args()
    platform = results.platform
    gamertag = results.gamertag
    
    singleRun(gamertag,platform)
