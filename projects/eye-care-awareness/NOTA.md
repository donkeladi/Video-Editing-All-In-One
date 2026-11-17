# Eye Care Awareness (DS Pharma) — nota projek
- Output: `output/eye-care-awareness.mp4` (1080x1920, 30fps, 47.6s, -14.6 LUFS) — tidak di-commit.
- Aliran: `matte_person.py` (RVM onnx, model: github.com/PeterL1n/RobustVideoMatting v1.0.0) → `align_script.py` → `build_edit.py render`.
- Hero text di BELAKANG orang (matte); panel bukti/carta di hadapan, ruang muka sentiasa bebas.
- Subtitle = ASR tempatan (faster-whisper small, `transcribe_local.py`) → `fix_timing.py` (betulkan ejaan, snap ke onset senyap). Teks ikut ucapan sebenar; ayat akhir "Saya dapatkan sekarang" kurang pasti — semak.
- Sumber: Pantai Hospital (22/05/2026) · NST 29/10/2025 (Ipsos Digital 2025).
- Dakwaan produk dihadkan kepada teks pek: "Traditionally used for healthy eyes"; no. daftar MAL22076147T.
