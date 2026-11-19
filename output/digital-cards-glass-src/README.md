# Digital Cards — Glassmorphism motion graphic

- Final video: `../digital-cards-glass.mp4` (1080×1920, 30 fps, 19.4 s, voiceover only, no music)
- `index.html`: the time-driven animation (`renderAt(t)`); open with `#play` to preview in a browser
- `assets/`: images generated on kie.ai with GPT Image-2 (`tools/gen_images.py`)
- `voiceover.mp3`: Gemini TTS (`gemini-3.1-flash-tts-preview`, voice Charon), pauses tightened (`tools/vo_edit.py`), sped up 6%, loudness-normalized
- `vo_marks.json`: phrase timings used to sync the animation

Render: `node tools/capture.js index.html frames 30 0 582`, then encode the frames with the voiceover in ffmpeg.
