# Eye Care (goji) — nota projek

Output: `output/eyecare_goji_tiktok_v3.mp4` (video penuh + overlay, gagap dibuang, kamera ikut muka; v1/v2 masih ada; tidak di-commit). 1080x1920, 30fps, 78.03s, H.264 CRF18, AAC 192k, ~-14 LUFS.
Bina semula: `python3 scripts/eyecare_audio.py && python3 scripts/eyecare_build.py` kemudian mux `work/video_noaudio.mp4` + `work/audio_final.wav`.
Input: `input/raw.mov` (salinan footage asal; fail asal tidak diubah).

## Keputusan
- Dialog tidak disusun semula. Hujung dipotong pada 74.44s (selepas "boleh cek sendiri") untuk buang ayat jualan "nak dapatkan ni... profile... bye bye" (74.5–78.8s) kerana brief: tiada jualan/CTA. Ini satu-satunya pembuangan dialog.
- Hook: slam "BUKAN HIASAN" pada frame 0 (tidak ada dalam audio; teks bawah muka). Goji jatuh ke mangkuk 4.05–5.0s.
- Layout v2: video utama penuh sepanjang masa; semua grafik overlay (kad lut sinar) di zon y~790-1410, bawah dagu, tiada di atas muka. Zoom 1.18x (hook/punchline), 1.08x (graf), 1.12x (end card).
- Warna disampel daripada gambar kotak: ungu #543996, teal #7FDDDA; ungu tua #2A1C4B (terbitan, 50% gelap).
- Font: Montserrat + Noto Sans (google/fonts, OFL) dalam assets/fonts.
- Efek: slam 2, flash 2, punch-in 3 (11.82, 22.52, 47.00), zoom-through 3 (3.9, 46.4, 71.6).

## Ejaan ditentukan daripada inferens (Whisper keliru, belum disahkan telinga)
zeaxanthin (15.5s), karotenoid (17.4s), "Paras zeaxanthin" (39.1s), "DS Pharma" (58s), "MAL" (68s), "ditingkatkan" (27.6s).

## v3 — potongan gagap & jarak muka
- Potongan (scripts/eyecare_edl.json, masa sumber): 34.68–35.97 ("buah go-" lalu diulang "buah beri goji ni") dan 38.80–42.50 ("para-zea-zea-" + senyap 2.5s sebelum diulang betul). Jumlah dibuang 4.99s; output 73.03s. Ubah EDL untuk tambah/kurang potongan, kemudian jalankan semula eyecare_audio.py dan eyecare_build.py.
- Muka dijejak setiap bingkai (scripts/face_track.py, YuNet, assets/models/yunet.onnx). Kamera dikunci pada dagu (y=640 output), zoom 1.30x/1.28x/1.24x, overlay bermula y>=820.
- Render mengukur jarak overlay-dagu pada setiap bingkai: min 153px, median 225px, 0 bingkai <40px (bingkai zoom-through dikecualikan).
- Kapsyen selepas potongan 2 ditetapkan semula: "Paras zeaxanthin" 42.70, "dan antioksidan" 43.74, "mereka naik" 44.72 (masa sumber).
