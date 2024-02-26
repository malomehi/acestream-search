# acestream-search
Simple script to find acestream links

## Install

Just checkout this repository and run:
```
pip install .
```

## Usage
```console
$ acestream-search --help
usage: acestream-search [-h]
                        [--category {american_football,athletics,bandy,baseball,basketball,beach_soccer,billiard,combat_sport,cricket,cycling,darts,field_hockey,floorball,football,futsal,golf,handball,ice_hockey,mma,netball,padel_tennis,racing,rugby_league,rugby_sevens,rugby_union,table_tennis,tennis,volleyball,winter_sport}]
                        [--search TEXT] [--hours HOURS] [--show-empty]

options:
  -h, --help            show this help message and exit
  --category {american_football,athletics,bandy,baseball,basketball,beach_soccer,billiard,combat_sport,cricket,cycling,darts,field_hockey,floorball,football,futsal,golf,handball,ice_hockey,mma,netball,padel_tennis,racing,rugby_league,rugby_sevens,rugby_union,table_tennis,tennis,volleyball,winter_sport}
                        Event category (default: all)
  --search TEXT         Text to look for in the event titles (default: any text)
  --hours HOURS         Events starting within the next number of hours. Started events are also included (2 hours ago max). (default: 1 hour)
  --show-empty          Show events with no available acestream links (default: False)
$
```
