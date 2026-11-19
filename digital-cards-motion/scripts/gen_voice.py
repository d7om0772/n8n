"""Generate the Arabic voiceover with Google AI Studio (Gemini TTS)."""
import base64, json, os, subprocess, sys, requests

KEY = os.environ["GEMINI_API_KEY"]
MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.8-flash-tts"
VOICE = sys.argv[2] if len(sys.argv) > 2 else "Charon"
OUT = os.path.join(os.path.dirname(__file__), "..", "audio")

SCRIPT = (
    "اقرأ النص التالي بلهجة سعودية بيضاء، بصوت إعلاني دافئ وواثق، بإيقاع حيوي وواضح، "
    "مع وقفات قصيرة عند النقاط:\n\n"
    "بطاقتك الرقمية... توصلك في ثواني!\n"
    "بدون شحن... وبدون انتظار.\n"
    "اختر بطاقتك... ادفع بأمان... واستلم الكود فورًا على جوالك.\n"
    "ألعاب... تسوّق... ترفيه... كلها في مكان واحد.\n"
    "البطاقات الرقمية... أسرع هدية، وأذكى اختيار."
)

body = {
    "contents": [{"parts": [{"text": SCRIPT}]}],
    "generationConfig": {
        "responseModalities": ["AUDIO"],
        "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
    },
}
r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                  headers={"x-goog-api-key": KEY, "Content-Type": "application/json"}, json=body, timeout=180)
d = r.json()
if "candidates" not in d:
    sys.exit(json.dumps(d, ensure_ascii=False)[:1500])
part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
print("mime:", part["mimeType"])
pcm = base64.b64decode(part["data"])
raw = os.path.join(OUT, f"vo_{VOICE}.pcm")
open(raw, "wb").write(pcm)
rate = 24000
for tok in part["mimeType"].split(";"):
    if tok.strip().startswith("rate="):
        rate = int(tok.split("=")[1])
wav = os.path.join(OUT, f"vo_{VOICE}.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", raw, wav], check=True)
os.remove(raw)
print(wav, subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                          capture_output=True, text=True).stdout.strip(), "s")
