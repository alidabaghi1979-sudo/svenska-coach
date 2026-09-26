# درس صوتی روزانه (daily_lesson) — بخشی از Svenska Coach 🇸🇪

هر شب خودکار (GitHub Actions) یک درس صوتی سوئدی می‌سازد و **مستقیم به اپ Svenska Coach می‌فرستد**:

```
موضوع بعدی (curriculum.json)
   ↓
متن درس با Claude (JSON دقیق)
   ↓
MP3 با صدای Sofie / Mattias / Hillevi (Azure)
   ↓
Google Drive  ← پخش روی گوشی
   ↓
Google Sheet «Ali Svenska Journal»
   ├─ تب lessons  → تب «📅 امروز» اپ
   └─ تب ordbank  → «📖 بانک کلمات» و مرور SRS
```

## داخل اپ چه می‌بینی

در تب **📅 امروز**، بالای صفحه بخش **🎧 درس صوتی روزانه** هست:

- پخش صدا، روی گوشی هم کار می‌کند.
- توضیح گرامر به فارسی، همراه با مثال‌ها.
- جدول واژه‌ها. این واژه‌ها خودکار به بانک کلمات اضافه شده‌اند و فردا در «مرور امروز» می‌آیند. واژه‌ای که قبلاً در بانک داشتی دوباره اضافه نمی‌شود.
- متن کامل درس.
- اسلایدر «چند درصدش رو فهمیدی؟» که نتیجه را در تب پیشرفت ثبت می‌کند.
- دکمه‌ی ارسال به Anki، فقط روی لپ‌تاپ و وقتی Anki باز است.
- فرم «➕ ساخت درس جدید» برای ساختن درس با موضوع دلخواه از روی گوشی. نیاز به توکن GitHub دارد (مرحله ۴).

**مربی** هم آخرین درس را می‌شناسد. کافی است بنویسی «بیا موقعیت درس امروز رو تمرین کنیم».

چرخه‌ی هفتگی:

| روز | دسته |
|---|---|
| دوشنبه، چهارشنبه، جمعه | روزمره (۲۶ موضوع) |
| سه‌شنبه، پنجشنبه | کار و مصاحبه (۲۱ موضوع) |
| شنبه | سبک آزمون SFI/SAS (۱۲ موضوع) |
| یکشنبه | آزاد (۹ موضوع) |

---

## مرحله ۱: کلید Azure Speech (رایگان)

1. برو به portal.azure.com و **Speech services** را جستجو کن، بعد **Create**.
2. تنظیمات:
   - Region: **Sweden Central**
   - Pricing tier: **Free F0** (ماهانه ۵۰۰ هزار کاراکتر رایگان؛ هر درس حدود ۵ هزار کاراکتر است)
3. برو به **Keys and Endpoint** و **KEY 1** را کپی کن.

## مرحله ۲: تست روی لپ‌تاپ (PowerShell)

روی لپ‌تاپ، کلید Claude، Google Sheet و Drive **خودکار از `.streamlit/secrets.toml` اپ خوانده می‌شوند**. فقط کلید Azure لازم است:

```powershell
cd "C:\Users\alida\My Drive\-ali-svenska\daily_lesson"
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

در `.env` فقط `TTS_API_KEY=` را با کلید Azure پر کن و ذخیره کن. بعد:

```powershell
python main.py next
python main.py run-daily
```

- `next` موضوع امروز را نشان می‌دهد و هزینه‌ای ندارد.
- `run-daily` درس امروز را می‌سازد. بعدش اپ را باز کن؛ درس باید در تب امروز باشد.

دستورهای دیگر:

```powershell
python main.py run-topic "Att köpa en begagnad cykel" "Adjektivets böjning"
python main.py run-daily --no-audio          # فقط متن (تست ارزان)
python main.py synthesize --lesson-id 1      # ساخت دوباره‌ی صدا
python main.py sync-sheets --lesson-id 1     # فرستادن دوباره به اپ
python main.py list
```

## مرحله ۳: اجرای شبانه با GitHub Actions

فایل `.github/workflows/daily-lesson.yml` در همین ریپو است. در GitHub برو به **Settings → Secrets and variables → Actions → New repository secret** و این‌ها را اضافه کن:

| Secret | مقدار از کجا |
|---|---|
| `LLM_API_KEY` | `api_key` زیر `[claude]` در secrets.toml |
| `TTS_API_KEY` | کلید Azure |
| `SVENSKA_SHEET_ID` | `svenska_sheet_id` در secrets.toml |
| `GCP_SERVICE_ACCOUNT_JSON` | فایل JSON سرویس‌اکانت، کامل (پایین را ببین) |
| `GDRIVE_CLIENT_ID` | زیر `[gdrive_oauth]` |
| `GDRIVE_CLIENT_SECRET` | زیر `[gdrive_oauth]` |
| `GDRIVE_REFRESH_TOKEN` | زیر `[gdrive_oauth]` |

**`GCP_SERVICE_ACCOUNT_JSON`:** همان فایل `.json` که موقع ساخت سرویس‌اکانت از Google Cloud دانلود کردی. بازش کن و **کل محتوا** را کپی کن و در Secret بچسبان. اگر فایل را نداری:

1. Google Cloud Console → IAM → Service Accounts → سرویس‌اکانتت
2. **Keys → Add key → JSON**

تست: تب **Actions → Daily Swedish lesson → Run workflow**.

از این به بعد هر شب حدود ساعت ۲ بامداد اجرا می‌شود. `state.json` و دیتابیس کوچک درس‌ها در پوشه‌ی `daily_lesson/data/` به ریپو کامیت می‌شوند تا شب بعد بداند نوبت کدام موضوع است. فایل‌های MP3 کامیت نمی‌شوند و فقط در Drive می‌روند.

> ریپو عمومی است. کلیدها در GitHub Secrets امن‌اند و هیچ‌وقت در کد یا لاگ دیده نمی‌شوند. فقط متن درس‌ها عمومی است.

## مرحله ۴ (اختیاری): دکمه‌ی «ساخت درس جدید» از گوشی

1. GitHub → Settings (پروفایل) → Developer settings → **Fine-grained tokens → Generate new token**
2. تنظیمات توکن:
   - Repository access: فقط `svenska-coach`
   - Permissions → **Actions: Read and write**
3. در Streamlit Cloud (و `secrets.toml` محلی) این را اضافه کن:
   ```toml
   [github]
   token = "github_pat_..."
   ```

## نکات Google Drive

- تا وقتی اپ OAuth در حالت **Testing** است، `refresh_token` بعد از ۷ روز باطل می‌شود و آپلود شبانه از کار می‌افتد. برای رفعش:
  1. Google Cloud → **OAuth consent screen → Publish app**
  2. `oauth_setup.py` را یک بار دیگر اجرا کن.
  3. توکن جدید را هم در secrets.toml بگذار، هم در GitHub Secret.
- اگر Drive تنظیم نشده باشد، درس ساخته می‌شود و در اپ دیده می‌شود، فقط بدون صدا.

## اگر چیزی خطا داد

- **ساخت صدا یا ارسال به اپ خطا داد:** درس گم نمی‌شود و اجرای Actions زرد یا قرمز می‌شود.
  - برای صدا: `synthesize --lesson-id N`
  - برای ارسال به اپ: `sync-sheets --lesson-id N`
- **بعد از ساخت درس، اپ فوراً آپدیت نشد:** اپ داده‌ها را ۲۰ ثانیه کش می‌کند. صفحه را رفرش کن.

## تست‌ها

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

تست `test_headers_match_app_sheets_helper` مطمئن می‌شود ستون‌های اپ و پایپ‌لاین همیشه یکی باشند.
