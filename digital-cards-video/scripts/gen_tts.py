import json, os, sys, base64, urllib.request, wave
KEY = os.environ["GEMINI_API_KEY"]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemini-3.8-flash-tts"
OUT = sys.argv[1]
LINES = [
 "رقميةٌ أم بلاستيكية؟ إليك الفرقَ بالأرقام.",
 "الرقميةُ تُصدَرُ في دقائق، والبلاستيكيةُ تحتاجُ أيامًا.",
 "وبالترميز، لا يصلُ رقمُ بطاقتِك الحقيقيُّ إلى التاجر.",
 "وفي السعودية، بلغتِ المدفوعاتُ الإلكترونيةُ تسعةً وسبعين بالمئة.",
 "الرقميةُ: أسرعُ، وأكثرُ أمانًا.",
]
STYLE = "Read in clear Modern Standard Arabic, as a confident, friendly tech explainer narrator, brisk energetic pace: "
ONLY = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
for i, line in enumerate(LINES, 1):
    if ONLY and i not in ONLY: continue
    if os.path.exists(os.path.join(OUT, f"s{i}.wav")) and not ONLY: continue
    body = {
            "contents": [{"parts": [{"text": line}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
              "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    import time, urllib.error
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            print("HTTP", e.code, msg, flush=True)
            if e.code != 429 or attempt == 5: raise
            time.sleep(20 * (attempt + 1))
    part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
    raw = base64.b64decode(part["data"])
    path = os.path.join(OUT, f"s{i}.wav")
    if raw[:4] == b"RIFF":
        open(path, "wb").write(raw)
    else:
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
    with wave.open(path) as w: print(i, part["mimeType"], round(w.getnframes()/w.getframerate(),2), "s", flush=True)
