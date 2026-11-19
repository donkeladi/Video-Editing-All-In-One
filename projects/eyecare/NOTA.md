# Eye Care — nota projek
Output: output/eyecare_tiktok_9x16.mp4 (1080x1920, 30fps, 59.70s, libx264 CRF18, aac 192k, -14.1 LUFS, TP -1.4 dBTP)
Bina semula: scripts/build_eyecare.py <video> work/render --workers 4 ; scripts/eyecare_audio.py <video> work/audio ;
  loudness: volume=3.45dB,alimiter=limit=0.84 ; mux guna ffmpeg concat + aac.
Sumber timecode: faster-whisper small (ASR tempatan), bukan ElevenLabs Scribe. Ketepatan ±0.1–0.2s.
Keputusan lalai (awak belum jawab): CTA lisan 52.72–56.54 TIDAK dikapsyen & tiada grafik; slam hook "MENTAH JE?" ikut brief;
  chip Kemenkes/Berita Harian ikut brief; end card = split + kad (bukan grafik penuh). Footage selepas 57.6s tidak digunakan (beku pada bingkai senyuman).
