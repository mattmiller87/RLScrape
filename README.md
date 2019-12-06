# rocketleaguescripts

main/main.py
 - required arguments:
   - gamertag
   - platform
 - optional arguments:
   - season(s)

As more options are designed for mass input/ouput, they will be added.
CSV:
 - asynccsv.py
   - asynchronous I/O (fastest)
   - in testing
 - synccsv.py
   - synchronous I/O
   - has been reliable so far
 - required arguments:
   - input csv file
 - optional arguments:
   - output csv file 
     - default is <datestamp>_RLTN.csv
   - season(s)
     - default is 13
   - returndata - playlists, games played and tier
     - defauls is All

Not using arguments will result in Memlo's stats being returned

Please check [requirements.txt](requirements.txt)
```
pip install -r requirements.txt 
```

Json dict creation; Example:
```
{'memlo': {
	9: {
		'Un-Ranked': {}, 
		'Ranked Duel 1v1': {
			'MMR': '1022', 
			'Games Played': '38'}, 
		'Ranked Doubles 2v2': {
			'MMR': '1481', 
			'Games Played': '111'}, 
		'Ranked Solo Standard 3v3': {
			'MMR': '1170', 
			'Games Played': '8'}, 
		'Ranked Standard 3v3': {
			'MMR': '1525', 
			'Games Played': '387'}}, 
	10: {
		'Un-Ranked': {
			'MMR': '2168', 
			'Games Played': '0', 
			'Rank': 'Unranked', 
			'Rank Division': 'Division I'}, 
		'Ranked Duel 1v1': {
			'MMR': '1081', 
			'Games Played': '8', 
			'Rank': 'Unranked', 
			'Rank Division': 'Division I'}, 
		'Ranked Doubles 2v2': {
			'MMR': '1495', 
			'Games Played': '102', 
			'Rank': 'Champion III', 
			'Rank Division': 'Division IV'}, 
		'Ranked Solo Standard 3v3': {
			'MMR': '1170', 
			'Games Played': '0', 
			'Rank': 'Unranked', 
			'Rank Division': 'Division I'}, 
		'Ranked Standard 3v3': {
			'MMR': '1470', 
			'Games Played': '178', 
			'Rank': 'Champion III', 
			'Rank Division': 'Division III'}
		}
	}
}
```
