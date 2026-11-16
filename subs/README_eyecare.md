# DS Pharma Eye Care — nota projek
Aliran: `eyecare_cut.py` (buang senyap + retake MAL) → transkrip faster-whisper medium pada cut.mp4 → `eyecare_frames.py` (zoom licin subpixel + matte orang) → `eyecare_build.py` (kad di belakang kepala, panel medical, subtitle, SFX, loudnorm -14 LUFS).
Matte: kekunci langsir statik (numpy/PIL), sah untuk zon kepala/bahu sahaja (y<760).
Zon selamat TikTok: atas >= y290, bawah <= y1410, kanan <= x1020.
Output: `output/eyecare_final.mp4`. Subtitle: `subs/eyecare.srt`.
