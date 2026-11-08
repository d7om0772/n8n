import json, os, sys, base64, urllib.request, time
v=base64.b64encode(open('test/review.mp4','rb').read()).decode()
prompt="""You are a strict creative director reviewing a 34-second vertical TikTok video for a Saudi PC-hardware account (Arabic, Saudi dialect voiceover).
Hard rules: (a) no images of living beings — no people, faces, eyes, heads, animals; (b) no music, only sound effects + voice.
Please check:
1) Any frame violating rule (a)? Give timestamps.
2) Any music (rule b)?
3) Sync: do on-screen Arabic words appear in time with the spoken words? Flag any noticeably early/late moments.
4) Readability: any text too small, cut off, overlapping, or covered by typical TikTok UI (bottom caption area / right-side buttons)?
5) Any visual glitch (blank frames, flicker, broken Arabic letter joining, misaligned elements)?
6) Top 5 concrete improvements, most impactful first.
Be concise, use timestamps."""
body={"contents":[{"parts":[{"inlineData":{"mimeType":"video/mp4","data":v}},{"text":prompt}]}]}
req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
for a in range(6):
    try: d=json.load(urllib.request.urlopen(req,timeout=400)); break
    except urllib.error.HTTPError as e: print("http",e.code,e.read()[:200]); time.sleep(20*(a+1))
print("".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"]))
