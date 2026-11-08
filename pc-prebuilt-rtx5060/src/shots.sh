#!/usr/bin/env bash
# Extracts the footage frames used by index.html (30 fps JPEG sequences).
# usage: FOOT=/path/to/pexels/mp4s OUT=shots ./shots.sh
set -euo pipefail
FOOT=${FOOT:?folder with the Pexels clips}; OUT=${OUT:-shots}
mk() { # name src ss dur vf
  mkdir -p "$OUT/$1"; rm -f "$OUT/$1"/*.jpg
  ffmpeg -v error -y -ss "$3" -t "$4" -i "$FOOT/$2.mp4" -vf "$5,fps=30" -q:v 3 -start_number 0 "$OUT/$1/%04d.jpg"
  echo "$1 $(ls "$OUT/$1" | wc -l)"
}
V="scale=1080:1920:flags=lanczos,unsharp=5:5:0.4"
# scene 1: prebuilt PC card (880x660 cover)
mk a_card    liquid_white 0.2 2.4 "scale=-2:660:flags=lanczos,crop=880:660"
# scene 4: GPU band (zoomed band over blurred fill), full frame 1080x1920
mk b_gpu     gpu_galax    2.0 2.9 "split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=28:2,eq=brightness=-0.18:saturation=1.2[bg];[b]scale=-2:620:flags=lanczos,crop=1080:620:(iw-1080)/2:0[fg];[bg][fg]overlay=0:540"
# scene 5: piece-by-piece montage (vertical crops)
mk c_mobo    mobo_gaming  1.0 0.6 "crop=608:1080:1060:0,$V"
mk c_ram     ram_rgb      2.0 0.6 "$V"
mk c_fans    fans_purple  3.0 0.6 "crop=608:1080:480:0,$V"
mk c_case    case_white   6.0 0.6 "crop=608:1080:240:0,$V"
# scene 7: result card thumbnails (300x220 cover)
T="scale=-2:220:flags=lanczos,crop=300:220"
mk t_liquid  liquid_white 2.0 5.4 "$T"
mk t_case    case_white   3.0 5.4 "$T"
mk t_orange  fans_orange  5.0 5.4 "$T"
# scene 8: RAM full screen (native vertical)
mk d_ram     ram_rgb      4.0 4.4 "$V"
# scene 9: list thumbnails (240x180)
L="scale=-2:180:flags=lanczos,crop=240:180"
mk e_mobo    mobo_gaming  4.0 5.6 "$L"
mk e_ram     ram_rgb      0.5 5.6 "crop=1080:810:0:500,scale=240:180:flags=lanczos"
# scene 11: CTA background
mk g_fans    fans_purple  8.0 4.4 "crop=608:1080:480:0,$V"
