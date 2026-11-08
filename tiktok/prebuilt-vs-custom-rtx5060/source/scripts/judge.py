import json, os, sys, base64, urllib.request, time
f = sys.argv[1]; model = sys.argv[2] if len(sys.argv)>2 else "gemini-3.8-flash"
audio = base64.b64encode(open(f,'rb').read()).decode()
prompt = """You are an expert in Gulf/Saudi Arabic dialects and audio QA. Listen to this Arabic voiceover.
1) Transcribe it verbatim in Arabic script exactly as spoken (write numbers/English terms as spoken, e.g. فيفتي سكستي).
2) Is the accent clearly Saudi (Najdi/Hijazi) colloquial? Rate 1-10 and note anything that sounds like MSA, Egyptian or Levantine.
3) Did the speaker pronounce "RTX 5060" and "DDR5" naturally? How exactly?
4) Any skipped, repeated, mispronounced or garbled words, odd intonation, clicks or artifacts?
5) Overall naturalness for a TikTok tech video, 1-10.
Expected script:
ما كنت أحب التجميعات الجاهزة، بس مع غلاء القطع، صارت خيار أذكى.
جمّعت جهاز بكرت RTX 5060 قطعة قطعة، وطلع معي ستة آلاف ريال.
بعدها دوّرت بأمازون السعودية، ولقيت تجميعات جاهزة بنفس الكرت، بأقل من خمسة آلاف.
وفيه خيارات برامات DDR5، بحدود خمسة آلاف ومية.
بس انتبه، أغلبها لوحاتها بسيطة، وبعضها رامات أقدم، فاقرا المواصفات قبل تشتري.
يعني لو ناوي تشتري هالفترة، الجاهز ممكن يوفّر عليك قريب ألف ريال.
وإذا تبغى أختار لك الأنسب، اكتب ميزانيتك بالتعليقات.
Answer concisely."""
body = {"contents":[{"parts":[{"inlineData":{"mimeType":"audio/wav","data":audio}},{"text":prompt}]}]}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
for a in range(5):
    try:
        d = json.load(urllib.request.urlopen(req, timeout=300)); break
    except urllib.error.HTTPError as e:
        print("http", e.code, e.read()[:200]); time.sleep(15*(a+1))
print("".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"]))
