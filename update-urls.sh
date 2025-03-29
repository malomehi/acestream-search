#!/usr/bin/env bash

regex='https\?://[a-zA-Z0-9./?=_&-]\+'
urls=$(grep -o "$regex" acestream_search/common/constants.py)

for url in $urls
do
    status_code=$(curl --silent --head --output /dev/null --write-out '%{http_code}' $url)
    echo "Status code for '$url': $status_code"
    if [ $status_code -eq 301 ]; then
        redirect_url=$(curl --silent --head --output /dev/null --write-out '%{redirect_url}' $url | head -c-1)
        if test -n "$(echo "$redirect_url" | grep -o "$regex")"; then
            sed -i "s,$url,$redirect_url,g" acestream_search/common/constants.py
            echo "Updated '$url' to '$redirect_url'"
        else
            echo "Invalid redirect url: $redirect_url"
        fi
    fi
done
