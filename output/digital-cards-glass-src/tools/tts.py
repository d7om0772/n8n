import os, json, base64, urllib.request, sys, wave
KEY=os.environ['GEMINI_API_KEY']; model=sys.argv[1]; voice=sys.argv[2]; out=sys.argv[3]; text=sys.argv[4]
body={"contents":[{"parts":[{"text":text}]}],
 "generationConfig":{"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":voice}}}}}
r=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",data=json.dumps(body).encode(),headers={'x-goog-api-key':KEY,'Content-Type':'application/json'})
d=json.load(urllib.request.urlopen(r,timeout=180))
part=d['candidates'][0]['content']['parts'][0]['inlineData']; print(part['mimeType'])
pcm=base64.b64decode(part['data'])
with wave.open(out,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
print(len(pcm)/48000,'sec')
