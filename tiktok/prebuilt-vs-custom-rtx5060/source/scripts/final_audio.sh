set -e
FC="[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,equalizer=f=3200:t=q:w=1.2:g=2,pan=stereo|c0=c0|c1=c0,apad=whole_dur=34[vv];[vv]asplit=2[v][vsc];[1:a]aresample=48000,highpass=f=55,equalizer=f=4500:t=q:w=1.4:g=-2.5[b0];[b0][vsc]sidechaincompress=threshold=0.04:ratio=3:attack=15:release=250[b];[v][b]amix=inputs=2:normalize=0:duration=first"
ffmpeg -v error -y -i tts/voice.wav -i sfx/bed.wav -filter_complex "$FC,atrim=0:34" -ar 48000 mix_pre.wav
J=$(ffmpeg -hide_banner -i mix_pre.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
II=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
set -- $II
ffmpeg -v error -y -i mix_pre.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true" -ar 48000 mix.wav
ffmpeg -hide_banner -i mix.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
