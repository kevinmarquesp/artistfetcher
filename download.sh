#!/usr/bin/env bash

JSON_LOCAL="${1}"
TARGET_PATH="${2}"
YTDLP_FLAGS="-x --audio-format mp3 --embed-thumbnail"

if ! yt-dlp --version &>/dev/null; then
  echo "Error: yt-dlp should be installed first."
  exit 1
elif ! [ -d "${JSON_LOCAL}" ]; then
  echo "Error: ${JSON_LOCAL} is not a directory or doesn't exists."
  exit 1
elif ! [ -d "${TARGET_PATH}" ]; then
  echo "Error: ${TARGET_PATH} is not a directory or doesn't exists."
  exit 1
fi

# NOTE: Some characters is special to bash, so they shouldn't be in the final
# file name. But `'` is special for the `xargs` command, it should not be in
# the file name by any reasons.

cat "${JSON_LOCAL}"/*.json |
  jq -rc '.' |
  while read -r data; do
    local_path=$(jq -r ".local_path" <<<"${data}" | sed "s/'/'\\\\''/g")
    video_id=$(jq -r ".song_video_id" <<<"${data}")

    echo "${TARGET_PATH}/${local_path}" "-- ${video_id}"
  done |
  xargs -I{} -P12 -- bash -c "yt-dlp ${YTDLP_FLAGS} --paths {}"
