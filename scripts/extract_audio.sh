#!/usr/bin/env bash
# Ekstrak audio mono 16k mp3 untuk transkripsi
set -euo pipefail
mkdir -p work
out="work/$(basename "${1%.*}").mp3"
ffmpeg -y -i "$1" -vn -ac 1 -ar 16000 -b:a 64k "$out"
echo "$out"
