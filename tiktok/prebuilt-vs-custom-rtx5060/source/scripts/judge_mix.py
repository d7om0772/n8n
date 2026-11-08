import json, os, sys, base64, urllib.request, time
parts=[]
for label,f in [("CLIP A (sound-effects bed only, boosted)","test/bed.mp3"),("CLIP B (final mix: voiceover + effects)","test/mix.mp3")]:
    parts.append({"text":label})
    parts.append({"inlineData":{"mimeType":"audio/mp3","data":base64.b64encode(open(f,'rb').read()).decode()}})
parts.append({"text":"""You are an audio QA engineer for a TikTok tech video. Rules: the soundtrack must contain NO music at all (no melodies, chords, beats, jingles or musical loops) — only sound effects and voice.
1) Clip A: does it contain anything that could be perceived as music (melody, chord progression, rhythmic beat, jingle)? List timestamps of anything borderline.
2) Clip A: describe the kinds of effects you hear and flag any that sound harsh, clipped, buzzy-ugly, or unnatural, with timestamps.
3) Clip B: is the voice always clearly intelligible over the effects? Any moment where an effect masks words (timestamps)? Are effects too loud or too quiet overall relative to voice (give a dB suggestion)?
Be concise and specific."""})
body={"contents":[{"parts":parts}]}
req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
for a in range(6):
    try: d=json.load(urllib.request.urlopen(req,timeout=300)); break
    except urllib.error.HTTPError as e: print("http",e.code); time.sleep(20*(a+1))
print("".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"]))
