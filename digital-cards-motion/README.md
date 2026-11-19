# موشن جرافيك: ٣ أخطاء شائعة عند شراء البطاقات الرقمية

فيديو عمودي 1080×1920، مدته 17.2 ثانية، بأسلوب دفتر الملاحظات (ورق مسطّر ومربعات، خطوط سوداء يدوية، لمسات أصفر وبيج).

- **الصوت:** Google AI Studio (`gemini-3.8-flash-tts`، صوت Puck، بلهجة سعودية بيضاء) بدون موسيقى.
- **الرسومات:** kie.ai، نموذج `gpt-image-2-text-to-image`. كلها جمادات، بدون ذوات أرواح.
- **الحركة:** رسم تدريجي (Line Drawing) يتبع مسار القلم، نصوص تُكتب بالقلم من اليمين لليسار، أسهم وخطوط تتحرك بين العناصر، وانتقال بين المشاهد بتقليب صفحات الدفتر.

الناتج: `output/digital-cards-notebook.mp4`

## إعادة البناء
```bash
python3 src/tts.py gemini-3.8-flash-tts Puck audio/voice.wav   # يحتاج GEMINI_API_KEY
python3 src/kie.py                                              # يحتاج KIE_AI_API_KEY
node src/build_text.js && python3 src/ink.py
node src/render.js video output/digital-cards-notebook.mp4 30
```
