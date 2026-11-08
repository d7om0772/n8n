import json, os, sys, base64, urllib.request, wave
model = sys.argv[1]; out = sys.argv[2]; variant = sys.argv[3] if len(sys.argv) > 3 else "a"
script = """ما كنت أحب التجميعات الجاهزة، بس مع غلاء القطع، صارت خيار أذكى.
جمّعت جهاز بكرت RTX 5060 قطعة قطعة، وطلع معي ستة آلاف ريال.
بعدها دوّرت بأمازون السعودية، ولقيت تجميعات جاهزة بنفس الكرت، بأقل من خمسة آلاف.
وفيه خيارات برامات DDR5، بحدود خمسة آلاف ومية.
بس انتبه، أغلبها لوحاتها بسيطة، وبعضها رامات أقدم، فاقرا المواصفات قبل تشتري.
يعني لو ناوي تشتري هالفترة، الجاهز ممكن يوفّر عليك قريب ألف ريال.
وإذا تبغى أختار لك الأنسب، اكتب ميزانيتك بالتعليقات."""
notes = {
"a": """Read the following transcript in a natural Saudi Arabic dialect (Najdi / Riyadh accent, everyday spoken Saudi, NOT Modern Standard Arabic, not Egyptian or Levantine). Style: a confident Saudi tech creator on TikTok talking about PC builds — energetic but relaxed, conversational, clear, slightly fast pace, with short natural pauses at commas and full stops. Pronounce "RTX 5060" as "آر تي إكس فيفتي سكستي" and "DDR5" as "دي دي آر فايف". Say "ومية" as "وميّة" (one hundred). Read only the transcript, nothing else.""",
"b": """You are a Saudi TikTok tech creator from Riyadh. Speak this in authentic Saudi colloquial dialect (لهجة سعودية نجدية بيضاء), punchy and engaging, with a slightly quick rhythm and natural micro-pauses at the commas, emphasising the numbers and prices. Pronounce "RTX 5060" as "آر تي إكس فيفتي سكستي" and "DDR5" as "دي دي آر فايف". Read only the transcript.""",
}[variant]
body = {
  "contents": [{"parts": [{"text": notes + "\n\nTRANSCRIPT:\n" + script}]}],
  "generationConfig": {"responseModalities": ["AUDIO"],
     "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}}
}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
import time
for attempt in range(6):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        break
    except urllib.error.HTTPError as e:
        print("http", e.code, e.read()[:300]); time.sleep(20*(attempt+1))
part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
pcm = base64.b64decode(part["data"])
print(part.get("mimeType"), len(pcm))
if pcm[:4] == b"RIFF":
    open(out, "wb").write(pcm)
else:
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
print("ok", out)
