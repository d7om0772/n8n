# فيديو تيك توك: التجميعة الجاهزة ولا التجميع الذاتي؟ (RTX 5060)

| الملف | الوصف |
|---|---|
| `pc_prebuilt_rtx5060_tiktok.mp4` | الفيديو النهائي: 1080×1920 (9:16)، 30 إطار/ث، المدة 35 ث، الصوت مضبوط على ‎-14 LUFS |
| `cover.jpg` | غلاف مقترح (لقطة RTX 5060) |
| `voiceover/take1.wav` | التعليق الصوتي المستخدم: Google AI Studio، موديل `gemini-3.8-flash-tts`، صوت Charon، لهجة سعودية |
| `voiceover/take2.wav` | تيك ثاني أبطأ (38.7 ث)، احتياط |
| `sfx_manifest.json` | مؤثرات Openverse المختارة (CC0 / CC-BY) مع روابطها |
| `src/` | المشروع كامل لإعادة التصدير |

## التسلسل (متزامن مع الكلام على مستوى الكلمة)
| الوقت | الجملة | الحركة |
|---|---|---|
| 0.0 | ما كنت أحب التجميعات الجاهزة | ضبابي ← واضح، ظهور من تحت، كرت ينكشف (لقطة تجميعة جاهزة) |
| 2.0 | بس مع غلاء القطع | خفيف ← عريض، خط أسعار يرتفع |
| 3.3 | صارت خيار أذكى | تبديل كلمة (غلط ← أذكى) + تحديد بلون |
| 5.0 | جمّعت جهاز بكرت RTX 5060 | كرت ينكشف للقطة كرت الشاشة، تحديد ← تعبئة |
| 7.5 | قطعة قطعة | قطعات سريعة (لوحة، رامات، تبريد، كيس) |
| 8.9 | وطلع معي ستة آلاف ريال | عدّاد من صفر لـ 6,000 |
| 11.4 | بعدها دوّرت بأمازون السعودية… بأقل من خمسة آلاف | كتابة في خانة البحث، نتائج تطلع من تحت، تحديد RTX 5060، السعر |
| 16.6 | وفيه خيارات برامات DDR5 بحدود خمسة آلاف ومية | لقطة رامات، DDR5 تحديد ← تعبئة، خفيف ← عريض، تبديل رقم 5,000 ← 5,100 |
| 20.7 | بس انتبه… فاقرا المواصفات قبل تشتري | glitch، غامق ← فاتح، قائمة تتحرك |
| 26.1 | يعني لو ناوي تشتري هالفترة… قريب ألف ريال | مقارنة أعمدة، الفرق، عدّاد 1,000 |
| 30.9 | وإذا تبغى أختار لك الأنسب، اكتب ميزانيتك بالتعليقات | حرف حرف، صندوق تعليق يُكتب فيه، سهم للتعليقات |

## القواعد
- ما فيه أي صور لذوات أرواح أو عيون أو رؤوس: كل اللقطات قطع كمبيوتر فقط (تم فحصها إطار بإطار كل ثانية)، واستُبعدت لقطة فيها يد ولقطة فيها عملات عليها وجه.
- ما فيه موسيقى: مؤثرات صوتية فقط (تم التحقق بفحص آلي للصوت).

## المؤثرات الصوتية
اخترت مؤثرات من Openverse (CC0) لكن ملفاتها مستضافة على Freesound (يرد 403) وWikimedia (يرد 429) من البيئة السحابية، فما قدرت أحمّلها.
المؤثرات في الفيديو الحالي مولّدة برمجياً (`src/sfx_synth.py`): ضوضاء مفلترة، نقرات، ضربات، رنّة معدنية واحدة، بدون أي لحن.
لو حمّلت ملفات `sfx_manifest.json` بنفسك، يكفي تعيد `mix.py` على مجلدها بدون إعادة تصدير الفيديو.

## مصادر اللقطات (Pexels، رخصة Pexels المجانية)
- Atakan Ozkan: https://www.pexels.com/video/close-up-video-of-a-computer-graphics-card-5466792/ و https://www.pexels.com/video/close-up-video-of-a-computer-central-processing-unit-5467579/
- Kamil Zubrzycki: https://www.pexels.com/video/cooling-fans-inside-a-computer-for-overheating-protection-3147349/
- Trishik Bose: https://www.pexels.com/video/high-performance-liquid-cooled-pc-setup-34821018/
- Pixabay: https://www.pexels.com/video/video-of-inside-of-cpu-854969/
- boudib islam: https://www.pexels.com/video/rgb-gaming-memory-of-a-computer-10470834/
- Joshua Malic: https://www.pexels.com/video/close-up-view-of-a-gaming-motherboard-11537352/

الخط: Rubik (Google Fonts، رخصة OFL).

## إعادة التصدير
```bash
cd src
./footage.sh /tmp/footage                       # تحميل اللقطات
FOOT=/tmp/footage OUT=shots ./shots.sh          # استخراج الإطارات
python sfx_synth.py                             # توليد المؤثرات (numpy + scipy)
node render.js video video_noaudio.mp4          # تصدير الصورة (Playwright + Chromium)
python mix.py ../voiceover/take1.wav mix.wav    # دمج الصوت مع المؤثرات وضبطه على -14 LUFS
ffmpeg -i video_noaudio.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest out.mp4
```
