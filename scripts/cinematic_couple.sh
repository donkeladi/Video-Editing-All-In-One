#!/usr/bin/env bash
# Edit sinematik 9:16 pasangan konvokesyen: 1 klip video + 11 gambar.
# Guna: cinematic_couple.sh <video.mov> <folder_gambar> <output.mp4>
# Nama pasangan: NAMES="Aisyah & Firdaus" ./cinematic_couple.sh ...
set -euo pipefail
VID="$1"; IMGDIR="$2"; OUT="$3"
NAMES="${NAMES:-}"
W=work/seg; mkdir -p "$W"
FS=/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf
FSB=/usr/share/fonts/truetype/freefont/FreeSerif.ttf
PD=3.6   # durasi setiap gambar
XF=0.7   # crossfade
FPS=30
GRADE="eq=contrast=1.05:saturation=0.95:gamma=1.08:brightness=0.015,colorbalance=rs=0.03:gs=0.0:bs=0.05:rh=0.05:gh=0.01:bh=-0.04,vignette=PI/6,noise=alls=3:allf=t,format=yuv420p"

# --- klip video (0-3.4s, perlahan 0.85x) ---
ffmpeg -v error -y -ss 0 -t 3.4 -i "$VID" -vf "setpts=PTS/0.85,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=$FPS,$GRADE" -an -c:v libx264 -crf 14 -preset medium $W/s00.mp4
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/s00.mp4)
echo "durasi klip video: $VD"

# --- gambar: fail:crop_x:crop_w:mod(in/out):crop_y ---
# urutan cerita
LIST=(
 "4e0eb109:300:1134:in"   # berjalan sambil saling pandang
 "650cf599:378:1134:out"  # berjalan dari belakang
 "588e7daa:580:844:in:0"  # landskap (crop potret)
 "1b162b43:250:1134:out"  # betulkan topi
 "1cbeeb0f:0:1134:in"     # siluet senyum
 "b02a8d29:483:1449:out"  # kejutan jambangan
 "8340c595:250:1134:in"   # serah jambangan
 "527b4534:300:1449:out"  # terima jambangan
 "5aa3e7b1:250:1134:in"   # potret dgn jambangan
 "0010d66c:240:1134:out"  # pose pipi
 "1f5732a2:300:1134:in"   # penutup: jambangan & kasut
)
i=0
for item in "${LIST[@]}"; do
  i=$((i+1)); IFS=: read -r id cx cw mode cy <<<"$item"
  f=$(ls "$IMGDIR"/*"$id"*image.jpg); ih=$(ffprobe -v error -show_entries stream=height -of csv=p=0 "$f")
  if [ -n "${cy:-}" ]; then ch=1500; else ch=$ih; fi; cy=${cy:-0}
  # crop 9:16 dari sumber
  cwh=$(( cw*16/9 )); [ $cwh -gt $ih ] && cwh=$ih
  [ "$ch" = 1500 ] && cwh=1500
  frames=$(python3 -c "print(int(($PD+$XF)*$FPS))")
  if [ "$mode" = in ]; then Z="min(zoom+0.00055,1.14)"; else Z="if(eq(on,1),1.14,max(zoom-0.00055,1.0))"; fi
  ffmpeg -v error -y -loop 1 -i "$f" -vf "crop=$cw:$cwh:$cx:$cy,scale=2160:-2:flags=lanczos,zoompan=z='$Z':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=$frames:s=1080x1920:fps=$FPS,$GRADE" -frames:v $frames -an -c:v libx264 -crf 14 -preset medium $W/s$(printf %02d $i).mp4
  echo "segmen $i siap"
done

# --- crossfade berantai ---
N=$i; inputs=(); for k in $(seq 0 $N); do inputs+=(-i $W/s$(printf %02d $k).mp4); done
fc=""; prev="[0:v]"; off=$(python3 -c "print($VD-$XF)")
for k in $(seq 1 $N); do
  fx=$([ $((k%2)) = 1 ] && echo fade || echo fadeblack); [ $k = $N ] && fx=fade
  fc+="${prev}[$k:v]xfade=transition=$fx:duration=$XF:offset=$off[v$k];"
  prev="[v$k]"; off=$(python3 -c "print(round($off+$PD,3))")
done
TOT=$(python3 -c "print(round($off-$PD+$PD+$XF,3))"); echo "jumlah ~ $TOT s"
# tajuk (masa mula segmen k = VD-XF+(k-1)*PD)
st() { python3 -c "print(round($VD-$XF+($1-1)*$PD,2))"; }
cap() { # teks mula tamat saiz y font
  echo "drawtext=fontfile=$5:text='$1':fontsize=$4:fontcolor=white@0.97:shadowcolor=black@0.7:shadowx=2:shadowy=3:borderw=1:bordercolor=black@0.25:x=(w-text_w)/2:y=$6:enable='between(t,$2,$3)':alpha='if(lt(t,$2+0.7),(t-$2)/0.7,if(gt(t,$3-0.7),($3-t)/0.7,1))'"
}
E1=$(st 4); E2=$(st 8); E3=$(st 11)
CAPS="$(cap 'Konvokesyen 2026' 0.8 3.6 96 $FS h*0.76),$(cap 'Setiap langkah, bersama.' $(st 2) $(python3 -c "print($(st 2)+3.2)") 68 $FS h*0.82),$(cap 'Bangga dengan kamu.' $(st 8) $(python3 -c "print($(st 8)+3.2)") 68 $FS h*0.82),$(cap 'Terima kasih, kerana sentiasa ada.' $E3 $(python3 -c "print($E3+3.2)") 62 $FS h*0.16)"
[ -n "$NAMES" ] && CAPS+=",$(cap "$NAMES" $(python3 -c "print($E3+0.6)") $(python3 -c "print($TOT-0.4)") 64 $FS h*0.72)"
fc+="${prev}${CAPS},fade=t=in:st=0:d=0.9,fade=t=out:st=$(python3 -c "print($TOT-1.4)"):d=1.2[vout]"
ffmpeg -v error -y "${inputs[@]}" -filter_complex "$fc" -map "[vout]" -an -c:v libx264 -crf 20 -preset slow -maxrate 16M -bufsize 32M -pix_fmt yuv420p work/video_noaudio.mp4

# --- audio: muzik + ambien asal 3.4s pertama ---
python3 scripts/music_pad.py work/music.wav "$TOT"
ffmpeg -v error -y -i work/music.wav -ss 0 -t 3.4 -i "$VID" -filter_complex "[0:a]aecho=0.8:0.7:90|220:0.35|0.2,lowpass=f=9000[m];[1:a]volume=0.5,afade=t=out:st=2.4:d=1.0,apad[a];[m][a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]" -map "[aout]" -c:a aac -b:a 192k work/audio.m4a
ffmpeg -v error -y -i work/video_noaudio.mp4 -i work/audio.m4a -c copy -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size:stream=width,height,codec_name -of default=nw=1 "$OUT"
