# Eye Care — nota projek
Output: output/eyecare_tiktok_9x16.mp4 (1080x1920, 30fps, 59.70s, libx264 CRF18, aac 192k, -14.1 LUFS, TP -1.4 dBTP)
Bina semula: scripts/build_eyecare.py <video> work/render --workers 4 ; scripts/eyecare_audio.py <video> work/audio ;
  loudness: volume=3.45dB,alimiter=limit=0.84 ; mux guna ffmpeg concat + aac.
Sumber timecode: faster-whisper small (ASR tempatan), bukan ElevenLabs Scribe. Ketepatan ±0.1–0.2s.
Keputusan lalai (awak belum jawab): CTA lisan 52.72–56.54 TIDAK dikapsyen & tiada grafik; slam hook "MENTAH JE?" ikut brief;
  chip Kemenkes/Berita Harian ikut brief; end card = split + kad (bukan grafik penuh). Footage selepas 57.6s tidak digunakan (beku pada bingkai senyuman).

## v2 — penyampai saiz asal, grafik di belakang (output/eyecare_tiktok_9x16_v2.mp4)
- Matte MODNet (ONNX, Apache-2.0): scripts/eyecare_matte.py -> work/matte/ (model: huggingface.co/Xenova/modnet -> work/models/modnet.onnx)
- Render: scripts/build_eyecare_v2.py <video> work/render2 --workers 4 ; timeline: scripts/eyecare_timeline_v2.py ; audio sama (EYECARE_TIMELINE=eyecare_timeline_v2).
- Penyampai skala 1.0 (anjak ke bawah 290px untuk ruang grafik); push 3.5% + 3 punch-in 12% kekal. Latar langsir diganti latar jenama.
- Versi split (v1) kekal: output/eyecare_tiktok_9x16.mp4

## v3 — bahan rujukan pengguna (output/eyecare_tiktok_9x16_v3.mp4)
- Foto bahan (lobak merah, avokado, goji, eyebright) + petikan Berita Harian (27 Julai 2019) dibekalkan pengguna -> assets/ref/ (TIDAK di-commit: hak cipta pihak ketiga).
- Nod lobak/avokado guna foto bulat; kad petikan akhbar (38.84–43.2s) dengan "menyerap lemak larut" diserlahkan (kotak teal); 4 jubin kandungan label (60/15/50/40mg) + chip "Sumber: label produk".
- Pengesahan sumber: artikel BH 27/7/2019 "Avokado, kekal berat badan ideal" menyebut avokado "berupaya menyerap lemak larut" dan "kaya dengan lemak baik". Dakwaan mata/katarak/tekanan darah dalam artikel TIDAK digunakan.
