# acestream-search
Simple tool to scrape acestream links from HTML content

## Install

Just run the following command in your python virtual environment:
```
pip install git+https://github.com/malomehi/acestream-search --upgrade
```

Alternatively download the executable binary files from the [release page](https://github.com/malomehi/acestream-search/releases)

## Usage

### Console Tool

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

### GUI Tool

```console
$ acestream-search-gui
```

![imagen](https://github.com/malomehi/acestream-search/assets/1456960/a66aa7f2-e8ea-403d-860c-b9aef98a5539)

## Collaborators

- [@dressi46](https://github.com/dressi46): GUI tool proposal and initial implementation
