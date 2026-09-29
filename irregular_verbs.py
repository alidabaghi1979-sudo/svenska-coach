"""
فعل‌های بی‌قاعده‌ی سوئدی — از Rivstart A1+A2 Verblista.
هر آیتم: مصدر، صرف (حال، گذشته‌ی ساده، فوق‌ماضی)، معنی فارسی.
"""

IRREGULAR_VERBS = [
    # --- Verb grupp 4a (it-verb) ---
    {"word": "binda", "forms": "binder, band, bundit", "meaning_fa": "بستن"},
    {"word": "dricka", "forms": "dricker, drack, druckit", "meaning_fa": "نوشیدن"},
    {"word": "finnas", "forms": "finns, fanns, funnits", "meaning_fa": "وجود داشتن"},
    {"word": "försvinna", "forms": "försvinner, försvann, försvunnit", "meaning_fa": "ناپدید شدن"},
    {"word": "hinna", "forms": "hinner, hann, hunnit", "meaning_fa": "فرصت رسیدن به کاری"},
    {"word": "sitta", "forms": "sitter, satt, suttit", "meaning_fa": "نشستن"},
    {"word": "slippa", "forms": "slipper, slapp, sluppit", "meaning_fa": "مجبور نبودن، معاف بودن"},
    {"word": "springa", "forms": "springer, sprang, sprungit", "meaning_fa": "دویدن"},
    {"word": "vinna", "forms": "vinner, vann, vunnit", "meaning_fa": "بردن، پیروز شدن"},

    {"word": "beskriva", "forms": "beskriver, beskrev, beskrivit", "meaning_fa": "توصیف کردن"},
    {"word": "bli", "forms": "blir, blev, blivit", "meaning_fa": "شدن"},
    {"word": "rida", "forms": "rider, red, ridit", "meaning_fa": "اسب‌سواری کردن"},
    {"word": "riva", "forms": "river, rev, rivit", "meaning_fa": "خراب کردن، پاره کردن"},
    {"word": "skina", "forms": "skiner, sken, skinit", "meaning_fa": "درخشیدن (خورشید)"},
    {"word": "skrika", "forms": "skriker, skrek, skrikit", "meaning_fa": "جیغ زدن"},
    {"word": "skriva", "forms": "skriver, skrev, skrivit", "meaning_fa": "نوشتن"},
    {"word": "sprida", "forms": "sprider, spred, spridit", "meaning_fa": "پخش کردن"},
    {"word": "stiga", "forms": "stiger, steg, stigit", "meaning_fa": "بالا رفتن، قدم گذاشتن"},
    {"word": "vrida", "forms": "vrider, vred, vridit", "meaning_fa": "پیچاندن، چرخاندن"},

    {"word": "försova sig", "forms": "försover, försov, försovit", "meaning_fa": "خواب ماندن"},
    {"word": "komma", "forms": "kommer, kom, kommit", "meaning_fa": "آمدن"},
    {"word": "sova", "forms": "sover, sov, sovit", "meaning_fa": "خوابیدن"},
    {"word": "återkomma", "forms": "återkommer, återkom, återkommit", "meaning_fa": "برگشتن، دوباره آمدن"},

    {"word": "bjuda", "forms": "bjuder, bjöd, bjudit", "meaning_fa": "دعوت کردن، تعارف کردن"},
    {"word": "dammsuga", "forms": "dammsuger, dammsög, dammsugit", "meaning_fa": "جارو برقی کشیدن"},
    {"word": "flyga", "forms": "flyger, flög, flugit", "meaning_fa": "پرواز کردن"},
    {"word": "frysa", "forms": "fryser, frös, frusit", "meaning_fa": "یخ زدن، سردش بودن"},
    {"word": "krypa", "forms": "kryper, kröp, krupit", "meaning_fa": "خزیدن، چهاردست‌وپا رفتن"},
    {"word": "hugga", "forms": "hugger, högg, huggit", "meaning_fa": "بریدن، تبر زدن"},
    {"word": "sjunga", "forms": "sjunger, sjöng, sjungit", "meaning_fa": "آواز خواندن"},
    {"word": "sjunka", "forms": "sjunker, sjönk, sjunkit", "meaning_fa": "غرق شدن، فرو رفتن"},
    {"word": "skjuta", "forms": "skjuter, sköt, skjutit", "meaning_fa": "شلیک کردن، هل دادن"},
    {"word": "stryka", "forms": "stryker, strök, strukit", "meaning_fa": "اتو کردن، نوازش کردن"},

    {"word": "dra", "forms": "drar, drog, dragit", "meaning_fa": "کشیدن"},
    {"word": "föreslå", "forms": "föreslår, föreslog, föreslagit", "meaning_fa": "پیشنهاد دادن"},
    {"word": "slå", "forms": "slår, slog, slagit", "meaning_fa": "زدن، ضربه زدن"},
    {"word": "ta", "forms": "tar, tog, tagit", "meaning_fa": "گرفتن"},

    {"word": "gråta", "forms": "gråter, grät, gråtit", "meaning_fa": "گریه کردن"},
    {"word": "låta", "forms": "låter, lät, låtit", "meaning_fa": "اجازه دادن، به‌نظر رسیدن (صدا)"},

    {"word": "falla", "forms": "faller, föll, fallit", "meaning_fa": "افتادن"},
    {"word": "hålla", "forms": "håller, höll, hållit", "meaning_fa": "نگه داشتن"},

    {"word": "äta", "forms": "äter, åt, ätit", "meaning_fa": "خوردن"},

    # --- Verb grupp 4b (special) ---
    {"word": "vara", "forms": "är, var, varit", "meaning_fa": "بودن"},
    {"word": "be", "forms": "ber, bad, bett", "meaning_fa": "خواهش کردن، دعا کردن"},
    {"word": "bestå", "forms": "består, bestod, bestått", "meaning_fa": "تشکیل شدن از"},
    {"word": "böra", "forms": "bör, borde, —", "meaning_fa": "بایستن (باید)"},
    {"word": "dö", "forms": "dör, dog, dött", "meaning_fa": "مردن"},
    {"word": "fortsätta", "forms": "fortsätter, fortsatte, fortsatt", "meaning_fa": "ادامه دادن"},
    {"word": "få", "forms": "får, fick, fått", "meaning_fa": "گرفتن، اجازه داشتن"},
    {"word": "förstå", "forms": "förstår, förstod, förstått", "meaning_fa": "فهمیدن"},
    {"word": "ge", "forms": "ger, gav, gett/givit", "meaning_fa": "دادن"},
    {"word": "gå", "forms": "går, gick, gått", "meaning_fa": "رفتن، پیاده رفتن"},
    {"word": "göra", "forms": "gör, gjorde, gjort", "meaning_fa": "انجام دادن"},
    {"word": "ha", "forms": "har, hade, haft", "meaning_fa": "داشتن"},
    {"word": "heta", "forms": "heter, hette, hetat", "meaning_fa": "نام داشتن"},
    {"word": "kunna", "forms": "kan, kunde, kunnat", "meaning_fa": "توانستن"},
    {"word": "ligga", "forms": "ligger, låg, legat", "meaning_fa": "دراز کشیدن، قرار داشتن"},
    {"word": "lägga", "forms": "lägger, la(de), lagt", "meaning_fa": "گذاشتن، دراز کردن"},
    {"word": "måste", "forms": "måste, måste, —", "meaning_fa": "مجبور بودن (باید)"},
    {"word": "pågå", "forms": "pågår, pågick, pågått", "meaning_fa": "در حال انجام بودن"},
    {"word": "se", "forms": "ser, såg, sett", "meaning_fa": "دیدن"},
    {"word": "ska", "forms": "ska, skulle, —", "meaning_fa": "قرار است (زمان آینده)"},
    {"word": "stå", "forms": "står, stod, stått", "meaning_fa": "ایستادن"},
    {"word": "säga", "forms": "säger, sa(de), sagt", "meaning_fa": "گفتن"},
    {"word": "sälja", "forms": "säljer, sålde, sålt", "meaning_fa": "فروختن"},
    {"word": "sätta", "forms": "sätter, satte, satt", "meaning_fa": "گذاشتن، قرار دادن"},
    {"word": "veta", "forms": "vet, visste, vetat", "meaning_fa": "دانستن"},
    {"word": "vilja", "forms": "vill, ville, velat", "meaning_fa": "خواستن"},
    {"word": "välja", "forms": "väljer, valde, valt", "meaning_fa": "انتخاب کردن"},
]
