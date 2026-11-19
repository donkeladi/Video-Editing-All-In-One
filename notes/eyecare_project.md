# Eye Care (goji) — nota projek

Output: `output/eyecare_goji_tiktok.mp4` (tidak di-commit). 1080x1920, 30fps, 78.03s, H.264 CRF18, AAC 192k, ~-14 LUFS.
Bina semula: `python3 scripts/eyecare_audio.py && python3 scripts/eyecare_build.py` kemudian mux `work/video_noaudio.mp4` + `work/audio_final.wav`.
Input: `input/raw.mov` (salinan footage asal; fail asal tidak diubah).

## Keputusan
- Dialog tidak disusun semula. Hujung dipotong pada 74.44s (selepas "boleh cek sendiri") untuk buang ayat jualan "nak dapatkan ni... profile... bye bye" (74.5–78.8s) kerana brief: tiada jualan/CTA. Ini satu-satunya pembuangan dialog.
- Hook: slam "BUKAN HIASAN" pada frame 0 (tidak ada dalam audio; teks bawah muka). Goji jatuh ke mangkuk 4.05–5.0s.
- Layout: L1 muka penuh 1.15x (0–3.9, 46.4–48.9, 71.6–74.44); L2 split 55/45 (selebihnya); end card = L2 dengan penyampai (bingkai senyum 79.1–79.3s asal) 74.44–78.04.
- Warna disampel daripada gambar kotak: ungu #543996, teal #7FDDDA; ungu tua #2A1C4B (terbitan, 50% gelap).
- Font: Montserrat + Noto Sans (google/fonts, OFL) dalam assets/fonts.
- Efek: slam 2, flash 2, punch-in 3 (11.82, 22.52, 47.00), zoom-through 3 (3.9, 46.4, 71.6).

## Ejaan ditentukan daripada inferens (Whisper keliru, belum disahkan telinga)
zeaxanthin (15.5s), karotenoid (17.4s), "Paras zeaxanthin" (39.1s), "DS Pharma" (58s), "MAL" (68s), "ditingkatkan" (27.6s).
