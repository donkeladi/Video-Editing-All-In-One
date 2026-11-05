# Video Editing All-In-One — arahan untuk Claude

Tugas: user bagi video (dalam `input/` atau link), Claude edit sampai siap, hasil dalam `output/`.

## Tool yang tersedia
- **ffmpeg/ffprobe** (local): potong, gabung, crop 9:16, speed, normalize audio, burn subtitle, overlay logo.
- **ElevenLabs MCP**: `creative_transcribe_audio` (transkrip/timestamp untuk subtitle), `creative_generate_speech` (voiceover/dubbing). Perlu `creative_list_voices` dulu untuk voice_id. Setiap generate guna kredit — jangan ulang.
- **Canva MCP**: thumbnail, intro/outro, design brand, export.
- **GitHub MCP**: commit/push skrip & projek ke repo ini.
- **Google Sheets MCP**: senarai shot / caption / jadual kandungan jika perlu.

## Aliran kerja standard
1. `scripts/probe.sh <video>` — semak resolusi, fps, durasi, audio.
2. `scripts/extract_audio.sh <video>` → transkrip guna ElevenLabs → `work/<nama>.srt`.
3. `scripts/cut_silence.sh <video>` — buang senyap (jump-cut).
4. `scripts/vertical.sh <video>` — 9:16 untuk TikTok/Reels/Shorts (kalau perlu).
5. `scripts/burn_subs.sh <video> <srt>` — subtitle dibakar.
6. `scripts/normalize_audio.sh <video>` — loudness -14 LUFS.
7. Export ke `output/`.

## Peraturan
- Jangan commit fail video; commit skrip, SRT, nota projek sahaja.
- Bahasa user: Bahasa Melayu. Subtitle ikut bahasa audio asal kecuali diminta lain.
- Kekal kualiti: libx264 CRF 18, aac 192k, kecuali diminta saiz kecil.
