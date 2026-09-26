# KLOVA – TikTok collage video

- `klova_tiktok.mp4`: final video. 1080×1920 (9:16), 30fps, 20.8s (same length as the voiceover). H.264 + AAC, loudness -14 LUFS.
- `cover.jpg`: suggested TikTok cover (hook frame).

## Rebuild

```bash
npm install
node render.js preview 1.7,5.9        # still frames -> preview/
node render.js full 0 624 video.mp4   # silent video (Chromium via Playwright)
node sfx.js 20.8 sfx.wav              # synthesizes the SFX from cues.json (written by render.js)
# mix: voice 100% + sfx.wav 42% + sfx_clicks.wav 30% -> +gain to -14 LUFS + limiter
```

- `main.js`: every scene and animation (GSAP), timed to the words in `assets/voice.srt`. It also emits the SFX cues.
- `sfx.js`: all sound effects are synthesized in code (click, whoosh, stamp, impact, buzzer, ding, sparkle, cha-ching, printer, ...). No background music.
  It writes two tracks: `sfx.wav` (effects bed, mixed at 0.42) and `sfx_clicks.wav` (the word clicks, mixed at **30%**; voice at 100%).
- Stickers: Fluent Emoji (MIT). Flags: flag-icons (MIT). Fonts: Google Fonts (OFL/Apache).
