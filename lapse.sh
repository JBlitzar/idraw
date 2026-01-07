#!/usr/bin/env bash

mkdir -p /tmp/tlt
# takes a picture every one second
rpicam-still --timelapse 1 --output /tmp/tlt/img%04d.jpg & 
PID=$!
uv run -m canny.test
kill $PID
ffmpeg -framerate 1 -i /tmp/tlt/img%04d.jpg -c:v libx264 out.mp4
