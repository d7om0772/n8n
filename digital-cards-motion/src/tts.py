import os, sys, json, base64, wave, urllib.request
model = sys.argv[1]; voice = sys.argv[2]; out = sys.argv[3]
script = open(os.path.join(os.path.dirname(__file__), 'narration.txt'), encoding='utf-8').read().strip()
prompt = ("Read aloud ONLY the Arabic text below (do not read this instruction). "
          "Style: friendly, clear, lightly energetic Saudi Gulf accent, brisk natural pace, "
          "short pauses between sentences.\n\n" + script)
body = {"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), method="POST",
    headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
resp = json.load(urllib.request.urlopen(req, timeout=180))
part = resp["candidates"][0]["content"]["parts"][0]["inlineData"]
pcm = base64.b64decode(part["data"])
if pcm[:4] == b"RIFF":
    open(out, "wb").write(pcm)
    import wave as _w; ww = _w.open(out); print(out, ww.getnframes()/ww.getframerate(), "sec"); sys.exit(0)
rate = 24000
mt = part.get("mimeType", "")
if "rate=" in mt: rate = int(mt.split("rate=")[1].split(";")[0])
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
print(out, mt, len(pcm) / (2 * rate), "sec")
