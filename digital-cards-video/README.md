# Digital cards — infographic motion video (19.8s, 1080×1920)

Final file: `digital_cards_motion.mp4`

- Voice: Gemini TTS (`gemini-3.8-flash-lite-tts`, voice "Charon"), via `scripts/gen_tts.py`
- Illustrations: kie.ai GPT Image 2 (`gpt-image-2-text-to-image`, transparent background), via `scripts/gen_images.py`
- Audio timing: `scripts/build_audio.py` (removes long pauses, time-stretches to fit under 20s, writes `timeline.json`)
- Animation: `index.html` (deterministic `seek(t)` timeline) rendered frame-by-frame by `scripts/render.cjs` (Playwright + ffmpeg)

Rebuild: `python3 scripts/build_audio.py && node scripts/render.cjs digital_cards_motion.mp4`

Stats source: SAMA (Saudi Central Bank), e-payments share of retail payments 70% (2023) → 79% (2024); 12.6B non-cash transactions in 2024.
