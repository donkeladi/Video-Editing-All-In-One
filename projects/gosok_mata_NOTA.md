# Gosok Mata — awareness (DS Pharma Eye Care)
- Input: `input/gosok_mata.mov` (1080x1920, 68s) → Output: `output/gosok_mata_awareness.mp4` (55.5s, -14 LUFS, CRF18).
- Potongan: senyap dibuang; bahagian tersasul (src 26.28–32.74 "kornea yang memanjang… eh bukan… betul lah") dibuang.
- Grafik di lapisan BELAKANG orang (matte MODNet, Apache-2.0) supaya tak lindung muka. Skrip: `scripts/awareness_build.py`.
- Sumber: Cleveland Clinic (screenshot sebenar, hero artikel Keratoconus). Berita Harian disekat Cloudflare → kad petikan (bukan screenshot).
- Fakta penting: Cleveland Clinic — kaitan gosok mata & keratoconus = *association*, pakar belum dapat membuktikan; overlay guna "ada kaitan".
- Semak: "bakul kuning" (audio kurang jelas), sebutan "KKM/hologram".
