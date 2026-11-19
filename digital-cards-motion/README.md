# موشن جرافيك — البطاقات الرقمية (كولاج غير ورقي)

فيديو عمودي 1080×1920، مدته 19 ثانية، بألوان فاتحة. فيه تعليق صوتي فقط، بدون موسيقى، وبدون أي صور لكائنات حية.

- **الفيديو النهائي:** `output/digital-cards.mp4`
- **الصوت:** Google AI Studio (Gemini TTS، النموذج `gemini-3.1-flash-tts-preview`، الصوت `Charon`). قصّرت الوقفات بين الجمل وسرّعت الإيقاع 3% عشان تكون المدة أقل من 20 ثانية.
- **العناصر:** kie.ai، النموذج GPT Image-2. 13 عنصر بخلفية شفافة (`assets/`).
- **الأسلوب:** كولاج رقمي غير ورقي. عناصر لامعة وأكريليك وزجاج مثلّج وهولوغرام، فوق بعضها بظلال ملونة، مع نوافذ زجاجية وشبكة نقاط. ما فيه ملمس ورق ولا حواف ممزقة.

## النص
> بطاقتك الرقمية… توصلك في ثواني! بدون شحن… وبدون انتظار.
> اختر بطاقتك… ادفع بأمان… واستلم الكود فورًا على جوالك.
> ألعاب… تسوّق… ترفيه… كلها في مكان واحد.
> البطاقات الرقمية… أسرع هدية، وأذكى اختيار.

## إعادة البناء
```bash
npm install
python3 scripts/gen_images.py          # يحتاج KIE_AI_API_KEY
python3 scripts/gen_voice.py gemini-3.1-flash-tts-preview Charon   # يحتاج GEMINI_API_KEY
python3 scripts/edit_voice.py          # يقصّر الوقفات ويطلع audio/timings.json
python3 scripts/prep_assets.py
node scripts/render.cjs                # Playwright + GSAP + ffmpeg
```
