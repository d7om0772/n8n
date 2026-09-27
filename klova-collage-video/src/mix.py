import subprocess, json, re
VOICE = '/root/.claude/uploads/959b3313-421c-592f-9838-5d110c51d22e/d3b2ae0a-generated_audio_1790456629846.wav'
DUR = 21.5
graph = ("[0:a]aresample=48000,apad=whole_dur={d},atrim=0:{d},asplit[v1][v2];"
         "[1:a]atrim=0:{d},volume=0.40[s];"
         "[s][v2]sidechaincompress=threshold=0.045:ratio=2.5:attack=4:release=220[sd];"
         "[v1][sd]amix=inputs=2:normalize=0:duration=first[m]").format(d=DUR)
def run(extra, out):
    cmd = ['ffmpeg', '-hide_banner', '-y', '-i', VOICE, '-i', 'out/sfx.wav', '-filter_complex', graph + extra, '-map', '[a]'] + out
    return subprocess.run(cmd, capture_output=True, text=True)
r = run(';[m]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[a]', ['-f', 'null', '-'])
js = json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr)[-1])
print('measured', js['input_i'], js['input_tp'])
lin = (';[m]loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:'
       'measured_thresh={input_thresh}:offset={target_offset}:linear=true,aresample=48000,aformat=channel_layouts=stereo[a]').format(**js)
r = run(lin, ['-c:a', 'pcm_s16le', 'out/mix.wav'])
print(r.returncode, r.stderr[-300:] if r.returncode else 'mix ok')
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'out/mix.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
print(r.stderr[-420:])
