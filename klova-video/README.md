# Klova — grid collage TikTok video (9:16)

- `klova_grid_collage.mp4` — final video, 1080×1920, 30 fps, 20.8 s (the voiceover's exact length), voiceover plus synthesized sound effects, no music.
- `render.html` — every frame drawn on a canvas by `render(t)`: the 2×3 grid, the six illustrated scenes, captions timed to the SRT, chips, and the CTA.
- `capture.js` — renders the frames with Playwright/Chromium: `node capture.js frames 30 20.8 4`.
- `sfx.py` — synthesizes the sound effects and mixes them with the voiceover: `python3 sfx.py voice.wav mix.wav sfx_only.wav`.

Encode:
```
ffmpeg -i mix.wav -af "volume=2.2dB,alimiter=limit=0.84:attack=3:release=60:level=disabled" mix_final.wav
ffmpeg -framerate 30 -i frames/f_%04d.png -i mix_final.wav -c:v libx264 -preset slow -crf 18 -maxrate 10M -bufsize 20M \
  -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest klova_grid_collage.mp4
```
Fonts: Tajawal (SIL OFL), from Google Fonts / Fontsource.
