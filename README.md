# acestream-search
Simple tool to scrape acestream links from HTML content

## Install

Just run the following command in your python virtual environment:
```
pip install git+https://github.com/malomehi/acestream-search --upgrade
```

Alternatively download the executable files from the [release page](https://github.com/malomehi/acestream-search/releases) (Linux and Windows operative systems are supported, x64)

## Usage

### Console Tool

```console
$ acestream-search --help
usage: acestream-search [-h]
                        [--category {american_football,athletics,aussie_rules,badminton,bandy,baseball,basketball,beach_soccer,beach_volleyball,boxing,climbing,billiard,combat_sport,cricket,cycling,darts,field_hockey,floorball,football,futsal,golf,handball,ice_hockey,mma,netball,padel_tennis,racing,rugby_league,rugby_sevens,rugby_union,table_tennis,tennis,triathlon,volleyball,water_polo,winter_sport}]
                        [--search TEXT] [--hours HOURS] [--show-empty]

options:
  -h, --help            show this help message and exit
  --category {american_football,athletics,aussie_rules,badminton,bandy,baseball,basketball,beach_soccer,beach_volleyball,boxing,climbing,billiard,combat_sport,cricket,cycling,darts,field_hockey,floorball,football,futsal,golf,handball,ice_hockey,mma,netball,padel_tennis,racing,rugby_league,rugby_sevens,rugby_union,table_tennis,tennis,triathlon,volleyball,water_polo,winter_sport}
                        Event category (default: all)
  --search TEXT         Text to look for in the event titles (default: any text)
  --hours HOURS         Events starting within the next number of hours. Started events are also included (3 hours ago max). (default: 1 hour)
  --show-empty          Show events with no available acestream links (default: False)
$
```

### GUI Tool

The GUI Tool, from version `v0.0.9` onwards, has an extra feature to send the links to remote Android devices (e.g. Android TV, Fire TV Stick, etc.). It can also send the links to the local device where the application is running.

Versions from `v2.0.0` onwards also include an experimental feature to search for channels and present them all in the results window.

In order to use these features, the local device (where the application runs) must have the Ace Stream application installed and Adroid devices (remote devices) must have remote ADB debugging enabled and the Ace Stream application installed.

You can google how to achieve the above.

The GUI tool will automatically discover Android devices in the local network with remote ADB debugging enabled. This will happen when the application starts.

```console
$ acestream-search-gui
```

![imagen](https://github.com/malomehi/acestream-search/assets/1456960/c30b4e3b-ab2e-4da6-822f-6dba12048294)

## Collaborators

- [@dressi46](https://github.com/dressi46): GUI tool proposal and initial implementation
