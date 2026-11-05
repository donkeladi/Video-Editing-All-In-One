#!/usr/bin/env bash
# Bakar subtitle. Guna: burn_subs.sh in.mp4 subs.srt [font_size=22]
set -euo pipefail
mkdir -p output
out="output/$(basename "${1%.*}")_sub.mp4"
ffmpeg -y -i "$1" -vf "subtitles=$2:force_style='FontSize=${3:-22},Bold=1,Outline=2,Alignment=2,MarginV=60'" -c:v libx264 -crf 18 -c:a copy "$out"
echo "$out"
