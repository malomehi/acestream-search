#!/usr/bin/env bash

MAX_RETRIES=5

regex='https\?://[a-zA-Z0-9./?=_&-]\+'
urls=$(grep -o "$regex" acestream_search/common/constants.py)

# Function to try incremental URLs when receiving 403
try_incremental_urls() {
    local original_url=$1
    local protocol=""
    local domain_part=""

    # Extract protocol (http:// or https://)
    if [[ $original_url =~ ^(https?://)(.+)$ ]]; then
        protocol="${BASH_REMATCH[1]}"
        domain_part="${BASH_REMATCH[2]}"
    else
        echo "Could not parse protocol from URL: $original_url"
        return 1
    fi

    # Check if domain contains a number (e.g., livetv876.me)
    if [[ $domain_part =~ ^([a-zA-Z]+)([0-9]+)(\..+)$ ]]; then
        local base_name="${BASH_REMATCH[1]}"
        local number="${BASH_REMATCH[2]}"
        local extension="${BASH_REMATCH[3]}"

        echo "Detected numeric URL pattern: ${base_name}${number}${extension}"
        echo "Trying up to $MAX_RETRIES incremental URLs..."

        # Try incremental URLs
        for ((i=1; i<=MAX_RETRIES; i++)); do
            local new_number=$((number + i))
            local new_url="${protocol}${base_name}${new_number}${extension}"

            echo "  Attempt $i/$MAX_RETRIES: Testing '$new_url'..."
            local new_status=$(curl --silent --head --output /dev/null --write-out '%{http_code}' "$new_url")
            echo "  Status code: $new_status"

            if [ $new_status -eq 200 ]; then
                echo "✓ Found working URL: $new_url"
                sed -i "s,$original_url,$new_url,g" acestream_search/common/constants.py
                echo "✓ Updated '$original_url' to '$new_url' in constants.py"
                return 0
            elif [ $new_status -eq 301 ]; then
                echo "  Received redirect (301), checking redirect URL..."
                local redirect_url=$(curl --silent --head --output /dev/null --write-out '%{redirect_url}' "$new_url" | head -c-1)
                if test -n "$(echo "$redirect_url" | grep -o "$regex")"; then
                    echo "✓ Found valid redirect: $redirect_url"
                    sed -i "s,$original_url,$redirect_url,g" acestream_search/common/constants.py
                    echo "✓ Updated '$original_url' to '$redirect_url' in constants.py"
                    return 0
                fi
            fi
        done

        echo "✗ All $MAX_RETRIES attempts failed for $original_url"
        return 1
    else
        echo "URL does not contain a numeric pattern, cannot try incremental URLs"
        return 1
    fi
}

for url in $urls
do
    status_code=$(curl --silent --head --output /dev/null --write-out '%{http_code}' $url)
    echo "Status code for '$url': $status_code"

    if [ $status_code -eq 403 ] || [ $status_code -eq 502 ]; then
        echo "Received $status_code, attempting incremental URL search..."
        try_incremental_urls "$url"
    elif [ $status_code -eq 301 ]; then
        redirect_url=$(curl --silent --head --output /dev/null --write-out '%{redirect_url}' $url | head -c-1)
        if test -n "$(echo "$redirect_url" | grep -o "$regex")"; then
            sed -i "s,$url,$redirect_url,g" acestream_search/common/constants.py
            echo "Updated '$url' to '$redirect_url'"
        else
            echo "Invalid redirect url: $redirect_url"
        fi
    fi
done
