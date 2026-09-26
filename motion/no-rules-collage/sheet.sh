#!/bin/bash
# usage: sheet.sh out.jpg dir f1 f2 ... (each tile 360x640, one row)
FF=/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
out=$1; dir=$2; shift 2; args=(); filt=""; n=0
for f in "$@"; do args+=(-i "$dir/f$(printf %04d $f).jpg"); filt+="[$n:v]scale=360:640[v$n];"; n=$((n+1)); done
ins=""; for ((i=0;i<n;i++)); do ins+="[v$i]"; done
$FF -loglevel error -y "${args[@]}" -filter_complex "${filt}${ins}hstack=inputs=$n" -frames:v 1 "$out"
