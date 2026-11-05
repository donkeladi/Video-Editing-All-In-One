#!/usr/bin/env bash
# Loudness -14 LUFS (standard sosial media)
set -euo pipefail
mkdir -p output
out="output/$(basename "${1%.*}")_norm.mp4"
ffmpeg -y -i "$1" -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 192k "$out"
echo "$out"
