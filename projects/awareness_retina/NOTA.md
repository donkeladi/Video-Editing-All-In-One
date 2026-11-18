# Awareness retina (BM)
- Sumber: input/awareness.mov (1080x1920, 53s) -> output/awareness_retina_final.mp4 (47.4s, termasuk end card 2s)
- Transkrip: faster-whisper (small) -> work/words.json; subtitle ikut ucapan sebenar.
- Potongan: senyap/jeda dibuang, pengulangan "bahagian pandangan," dibuang, "ataupun sekarang" di hujung dibuang, kerusi kosong di hujung dibuang.
- Zoom 100%/112% selang-seli pada titik potongan.
- Audio: highpass + denoise + compressor + loudnorm -14 LUFS.
- Bina semula: python3 -I scripts/build_awareness.py
