# Awareness retina (BM)
- Sumber: input/awareness.mov (1080x1920, 53s) -> output/awareness_retina_final.mp4 (49.2s, termasuk end card 2.4s)
- Transkrip: faster-whisper (small) -> work/words.json; subtitle ikut ucapan sebenar.
- Potongan: jeda dibuang, pengulangan "bahagian pandangan," dibuang, ayat penuh hingga "hari ini ataupun sekarang" dikekalkan, kerusi kosong di hujung dibuang.
- Zoom 100%/112% selang-seli pada titik potongan.
- Audio: highpass + denoise + compressor + loudnorm -14 LUFS.
- Bina semula: python3 -I scripts/build_awareness.py
- Grafik beranimasi (jujukan frame PNG), subtitle pop-in.
