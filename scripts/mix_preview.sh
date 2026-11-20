#!/usr/bin/env bash
# mix_preview.sh silent.mp4 cut.mp4 music.wav sfx.wav out.mp4  -- suara utama (dari cut.mp4) + muzik (duck) + SFX, -14 LUFS
set -euo pipefail
ffmpeg -y -v error -i "$1" -i "$2" -i "$3" -i "$4" -filter_complex \
"[1:a]aresample=44100,asplit[sp][sc];[2:a]volume=0.14[mu];[mu][sc]sidechaincompress=threshold=0.02:ratio=8:attack=8:release=350:makeup=1[md];[3:a]volume=0.10[fx];[sp][md][fx]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14.5:TP=-2.5:LRA=11,alimiter=limit=0.75:level=disabled[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest "$5"
