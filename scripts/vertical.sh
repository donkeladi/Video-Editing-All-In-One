#!/usr/bin/env bash
# Tukar ke 1080x1920 (crop tengah). Guna: vertical.sh in.mp4
set -euo pipefail
mkdir -p output
out="output/$(basename "${1%.*}")_9x16.mp4"
ffmpeg -y -i "$1" -vf "scale=-2:1920,crop=1080:1920" -c:v libx264 -crf 18 -c:a copy "$out"
echo "$out"
