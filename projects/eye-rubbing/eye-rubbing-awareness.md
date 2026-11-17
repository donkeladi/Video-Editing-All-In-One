# Eye Rubbing Awareness (DS Pharma Eye Care) — nota projek
- Input: video 1080x1920, 38.9s. Output: `output/eye-rubbing-awareness_9x16.mp4` (CRF 18, AAC 192k, -14 LUFS) — tidak di-commit.
- Overlay di BELAKANG orang guna mask MediaPipe (multiclass) + guided filter; skrip: `scripts/build_awareness.py`.
- Sumber fakta: Review of Optometry (19 Feb 2020) — 202 pesakit keratoconus vs 355 kawalan; gosok guna buku jari paling berkait; faktor lain: screen time, kerja malam, mata kering, alahan, posisi tidur.
- Carta "tahap kaitan" adalah ilustrasi kualitatif (bukan angka kajian) — dilabel pada carta.
- Transkrip: faster-whisper medium (ElevenLabs upload tidak tersedia); kapsyen ikut audio sebenar.
