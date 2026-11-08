from faster_whisper import WhisperModel
import json, sys
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8")
import numpy as np
audio=np.fromfile("tts/voice16.f32",dtype=np.float32)
segs, info = m.transcribe(audio, language="ar", word_timestamps=True, beam_size=5, initial_prompt="تجميعات بي سي، كرت شاشة، رامات، لوحة أم، ريال سعودي.", condition_on_previous_text=False)
words = []
for s in segs:
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)})
json.dump(words, open(f"tts/words2_{sys.argv[1]}.json", "w"), ensure_ascii=False, indent=0)
for w in words: print(w["s"], w["e"], w["w"])
