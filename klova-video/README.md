# KLOVA – TikTok collage video

- `klova_tiktok.mp4`: final video. 1080×1920 (9:16), 30fps, 20.8s (same length as the voiceover). H.264 + AAC, loudness -14 LUFS.
- `cover.jpg`: suggested TikTok cover (hook frame).

## Rebuild

```bash
npm install
node render.js preview 1.7,5.9        # still frames -> preview/
node render.js full 0 624 video.mp4   # silent video (Chromium via Playwright)
node sfx.js 20.8 sfx.wav              # synthesizes the SFX from cues.json (written by render.js)
# mix: voice + sfx*0.42 -> loudnorm -14 LUFS (see the commit message for the ffmpeg command)
```

- `main.js`: every scene and animation (GSAP), timed to the words in `assets/voice.srt`. It also emits the SFX cues.
- `sfx.js`: all sound effects are synthesized in code: pop, whoosh, stamp, impact, buzzer, ding, sparkle, cha-ching, printer, and so on. No background music.
- Stickers: Fluent Emoji (MIT). Flags: flag-icons (MIT). Fonts: Google Fonts (OFL/Apache).
