#!/usr/bin/env bash
# Downloads the Pexels clips used by shots.sh (free to use under the Pexels license).
set -euo pipefail
OUT=${1:-footage}; mkdir -p "$OUT"; cd "$OUT"
get() { [ -s "$1.mp4" ] || curl -sS -f -L -o "$1.mp4" "$2"; }
get gpu_galax    https://videos.pexels.com/video-files/5466792/5466792-hd_1920_1080_30fps.mp4
get fans_purple  https://videos.pexels.com/video-files/3147349/3147349-hd_1920_1080_25fps.mp4
get liquid_white https://videos.pexels.com/video-files/34821018/14762633_1920_1080_30fps.mp4
get case_white   https://videos.pexels.com/video-files/854969/854969-hd_1920_1080_24fps.mp4
get fans_orange  https://videos.pexels.com/video-files/5467579/5467579-hd_1920_1080_30fps.mp4
get ram_rgb      https://videos.pexels.com/video-files/10470834/10470834-hd_1080_1920_30fps.mp4
get mobo_gaming  https://videos.pexels.com/video-files/11537352/11537352-hd_1920_1080_30fps.mp4
