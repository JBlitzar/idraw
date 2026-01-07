#!/usr/bin/env bash

mkdir -p /tmp/tlt
# takes a picture every one second
rpicam-still --timelapse 3000 --timeout 0 --output /tmp/tlt/img%04d.jpg & 
PID=$!
uv run -m canny.test
kill $PID
ffmpeg -r 10 -f image2 -pattern_type glob -i '/tmp/tlt/*.jpg' -vf "hflip,vflip" -s 1280x720 -vcodec libx264 -crf 25 -pix_fmt yuv420p lapse.mp4
echo "Saved to lapse.mp4"
echo "rm /tmp/tlt/*.jpg"