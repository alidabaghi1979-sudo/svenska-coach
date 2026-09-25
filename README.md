# Svenska Coach

اپ یکپارچه‌ی تمرین سوئدی: داشبورد روزانه، بانک کلمات، خطاهای تکراری، نمودار پیشرفت، و مربی هوش مصنوعی — همه تو یه Streamlit app، دقیقاً مثل معماری AT Journal.

- **نسخه‌ی محلی (کامپیوتر)**: همه‌چیز فعاله، از جمله دانلود و رونویسی خودکار صوت
- **نسخه‌ی ابری (گوشی، از طریق مرورگر)**: بانک کلمات، خطاها، پیشرفت و مربی — بدون دانلود صوت (چون رونویسی با Whisper رو سرور رایگان جواب نمی‌ده)

هر دو نسخه از یه Google Sheet مشترک می‌خونن، پس هرجا هرچی رو تغییر بدی، همه‌جا هست.

## مرحله ۱: ساخت Google Sheet

1. یه Google Sheet جدید بساز، هر اسمی (مثلاً «Ali Svenska Journal»).
2. تب‌های داخلش رو خودِ اپ اولین بار که اجرا بشه خودکار می‌سازه — نیازی نیست دستی بسازی.
3. شیت رو با همون سرویس‌اکانتی که تو AT Journal داری به اشتراک بذار (Share → Editor):
   `ali-journal-sheets@gen-lang-client-0571200015.iam.gserviceaccount.com`
4. از آدرس شیت، بخش SHEET_ID رو کپی کن:
   `https://docs.google.com/spreadsheets/d/SHEET_ID_اینجاست/edit`

## مرحله ۲: گرفتن کلید Claude API

1. برو به console.anthropic.com و یه API key بساز.
2. این جدا از اشتراک claude.ai‌ته و بر اساس مصرف واقعی هزینه داره (برای چت روزانه‌ی کوتاه، هزینه‌ش ناچیزه چون از مدل Haiku استفاده می‌کنیم).

## مرحله ۳: تنظیم secrets (محلی)

1. فایل `.streamlit/secrets.toml.example` رو کپی کن و اسمش رو بذار `secrets.toml` (تو همون پوشه‌ی `.streamlit`).
2. مقادیر `svenska_sheet_id`، بلوک `gcp_service_account` (از همون فایل JSON سرویس‌اکانت AT Journal) و `claude.api_key` رو پر کن.

## مرحله ۴: اجرای محلی

```
pip install -r requirements.txt
pip install -r requirements-audio.txt
streamlit run app.py
```

مرورگر خودکار باز می‌شه رو `localhost:8501`.

## مرحله ۵: دیپلوی رو Streamlit Cloud (برای دسترسی از گوشی)

1. این پوشه رو به یه ریپازیتوری GitHub پوش کن (خصوصی، مثل ریپوی AT Journal). **secrets.toml رو پوش نکن** — تو `.gitignore` بذارش.
2. برو share.streamlit.io، ریپو رو وصل کن، `app.py` رو به‌عنوان فایل اصلی انتخاب کن.
3. تو تنظیمات اپ رو Streamlit Cloud، بخش Secrets رو باز کن و کل محتوای `secrets.toml` خودت رو اونجا پیست کن.
4. چون `requirements-audio.txt` رو کلود نصب نمی‌شه (فقط `requirements.txt` خونده می‌شه)، دکمه‌ی دانلود خودکار اونجا غیرفعال می‌مونه — طبق طراحی.
5. بعد از دیپلوی، یه لینک می‌گیری که از گوشی هم باز می‌شه.

## ساختار فایل‌ها

```
svenska_super_app/
├── app.py                          # اپ اصلی Streamlit (۵ تب)
├── sheets_helper.py                 # خواندن/نوشتن Google Sheets
├── coach.py                         # مربی هوش مصنوعی با Claude API
├── config.py                        # منابع صوتی (فقط محلی)
├── fetch_podcast.py                 # دانلود پادکست (فقط محلی)
├── fetch_youtube.py                 # دانلود یوتیوب (فقط محلی)
├── transcribe.py                    # رونویسی با Whisper (فقط محلی)
├── requirements.txt                 # وابستگی‌های سبک (کلود + محلی)
├── requirements-audio.txt           # وابستگی‌های سنگین (فقط محلی)
└── .streamlit/
    └── secrets.toml.example         # قالب کلیدهای محرمانه
```

## نکات

- تب «بانک کلمات» و «خطاهای من» با `st.data_editor` قابل ویرایش مستقیمن — بعد از تغییر، دکمه‌ی ذخیره رو بزن.
- تب «مربی» خودش کلمات و خطاهای اخیرت رو از شیت می‌خونه و تو پرامپتش می‌ذاره، پس بدون تکرار زمینه باهاش شروع به مکالمه کن.
- مدل مربی پیش‌فرض `claude-haiku-4-5` است (سریع و ارزون). اگه کیفیت مکالمه براش مهم‌تر از هزینه‌ست، تو `coach.py` مقدار `MODEL` رو به `claude-sonnet-5` تغییر بده.
