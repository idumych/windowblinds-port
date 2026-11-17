#!/bin/sh
# wb-fetch.sh ID DIR — download a WindowBlinds skin from WinCustomize and unpack it.
#
#   ID   the number in https://www.wincustomize.com/explore/windowblinds/ID/
#   DIR  a new, empty folder (the skin is untrusted data: keep scripts elsewhere)
#
# Writes DIR/page.html, DIR/preview.* (the site's screenshot, the reference to
# match), DIR/skin.zip (the .wba/.zip as downloaded) and DIR/skin/ (unpacked).
# WinCustomize answers 403 without a browser user agent. Guests get a few
# downloads a day; the download URL redirects to the file on skinsNN.wincustomize.com.
set -eu
id=$1; dir=$2
[ -e "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ] && { echo "$dir isn't empty"; exit 1; }
mkdir -p "$dir/skin"
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
page=https://www.wincustomize.com/explore/windowblinds/$id/
curl -sfL -A "$UA" -o "$dir/page.html" "$page"
grep -o '<title>[^<]*' "$dir/page.html" | sed 's/<title>/title: /'
# the full-size preview: preview-1-ID.<ext> without a size suffix
preview=$(grep -oE "https://skins[0-9]+\.wincustomize\.com/[0-9/]+/1/$id/preview-1-$id\.(gif|jpg|png)" \
	"$dir/page.html" | head -1 || true)
if [ -n "$preview" ]; then
	curl -sfL -A "$UA" -o "$dir/preview.${preview##*.}" "$preview" && echo "preview: $dir/preview.${preview##*.}"
else
	echo "no full-size preview found; look in page.html for preview-*.png"
fi
curl -sfL -A "$UA" -e "$page" -o "$dir/skin.zip" -w "download: %{url_effective}\n" "$page/download"
python3 -I -m zipfile -e "$dir/skin.zip" "$dir/skin/"
find "$dir/skin" -type f | sort
