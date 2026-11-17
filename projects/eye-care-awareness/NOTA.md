# Eye Care Awareness (DS Pharma) — nota projek
- Output: `output/eye-care-awareness.mp4` (1080x1920, 30fps, 47.6s, -14.6 LUFS) — tidak di-commit.
- Aliran: `matte_person.py` (RVM onnx, model: github.com/PeterL1n/RobustVideoMatting v1.0.0) → `align_script.py` → `build_edit.py render`.
- Hero text di BELAKANG orang (matte); panel bukti/carta di hadapan, ruang muka sentiasa bebas.
- Masa subtitle = ANGGARAN (silencedetect + skrip), bukan ASR. Ganti dengan transkrip ElevenLabs jika link video https tersedia.
- Sumber: Pantai Hospital (22/05/2026) · NST 29/10/2025 (Ipsos Digital 2025).
- Dakwaan produk dihadkan kepada teks pek: "Traditionally used for healthy eyes"; no. daftar MAL22076147T.
