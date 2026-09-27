#!/usr/bin/env bash
# Full rebuild: graded assets -> frames -> SFX mix -> final TikTok mp4.
# Needs: python3 (pillow numpy scipy), node + playwright (Chromium), ffmpeg with libx264.
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-../klova_matchcut_tiktok.mp4}
TMP=$(mktemp -d)

python3 prep.py
node render.js video "$TMP/video.mp4" 4          # also writes sfx_events.json
python3 sfx.py assets/voice.wav sfx_events.json "$TMP/mix.wav"

# two-pass loudness normalisation to -14 LUFS / -1.5 dBTP (TikTok level)
STATS=$(ffmpeg -hide_banner -i "$TMP/mix.wav" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
get() { echo "$STATS" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
ffmpeg -y -hide_banner -loglevel error -i "$TMP/mix.wav" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000" \
  "$TMP/mix_norm.wav"

ffmpeg -y -hide_banner -loglevel error -i "$TMP/video.mp4" -i "$TMP/mix_norm.wav" \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 -maxrate 16M -bufsize 32M -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
rm -rf "$TMP"
echo "built $OUT"
