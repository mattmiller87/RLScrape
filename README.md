# rocketleaguescripts
I have been making this more modular.

You can run rlscrape.py using arguments to pass gamertag and platform.

Alternatively, if you have a csv, you can use rlcsv.py and specify input,output csv.

Not using arguments will result in Memlo's stats being returned

Please check [requirements.txt](requirements.txt)
```
pip install -r requirements.txt 
```

Input CSV format for now must be
input: csv
* kwargs
* Tracker Link

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