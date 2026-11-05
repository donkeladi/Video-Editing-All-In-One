#!/usr/bin/env bash
set -euo pipefail
ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate -of default=nw=1 "$1"
