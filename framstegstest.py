"""
خودآزمایی‌های «Framstegstest» از کتاب Rivstart A1+A2 (Kopieringsunderlag).
فعلاً فقط Framstegstest 1 (فصل ۱-۳) — بقیه بعداً اضافه می‌شن.
هر تست از چند بخش (section) تشکیل شده: نوع mcq (چندگزینه‌ای) یا fill (جای خالی).
برای fill: هر آیتم {"prompt": "...", "answer": "...", "accept": [گزینه‌های قابل قبول دیگه]}
بعضی بخش‌ها یه "passage" هم دارن (متن کامل برای نمایش، فقط جنبه‌ی مرجع داره).
"""

FRAMSTEGSTEST_1 = {
    "title": "Framstegstest 1",
    "subtitle": "فصل ۱ تا ۳",
    "sections": [
        {
            "num": 1, "title": "Vad svarar man?", "type": "mcq",
            "instructions": "جواب مناسب رو انتخاب کن.",
            "items": [
                {"prompt": "Jag söker jobb på restaurang.",
                 "options": ["Jaha. Lycka till!", "Det var så lite.", "Tack så mycket."], "correct": 0},
                {"prompt": "Vad har du för yrke?",
                 "options": ["På förskola.", "Jag är ingenjör.", "Jag har två barn."], "correct": 1},
                {"prompt": "Hur dags börjar filmen?",
                 "options": ["Hon är kvart över sju.", "Den är kvart över sju.", "Kvart över sju."], "correct": 2},
                {"prompt": "Är du gift?",
                 "options": ["Nej, men jag är sambo.", "Ja, jag är singel.", "Nej, vi bor inte ihop."], "correct": 0},
                {"prompt": "Hur är läget?",
                 "options": ["Ja, precis.", "Helt okej, tack.", "Jaha, vad kul!"], "correct": 1},
                {"prompt": "När är du född?", "options": ["1990.", "I Malmö.", "25 år."], "correct": 0},
                {"prompt": "Tack så mycket.", "options": ["Ja, tack.", "Helt okej.", "Det var så lite."], "correct": 2},
                {"prompt": "Anders och jag bor inte ihop.", "options": ["Jaha.", "Nähä.", "Ja."], "correct": 1},
                {"prompt": "Var ligger Kiruna?",
                 "options": ["Ja, jag bor där.", "I norra Sverige.", "Svenska och finska."], "correct": 1},
                {"prompt": "Ha det så bra!", "options": ["Du med!", "Bara bra, tack.", "Det är toppen!"], "correct": 0},
            ],
        },
        {
            "num": 2, "title": "Frågeord", "type": "fill",
            "instructions": "کلمه‌ی پرسشی درست رو تو جای خالی بنویس: Hur, När, Vad, Var, Varför, Varifrån, Vilken, Vilket (می‌تونی یه کلمه رو چندبار استفاده کنی).",
            "items": [
                {"prompt": "___ kommer din sambo? – Från Portugal.", "answer": "Varifrån"},
                {"prompt": "___ mår du? – Så där. Jag är lite trött.", "answer": "Hur"},
                {"prompt": "___ har du för telefonnummer? – 072-12 42 33.", "answer": "Vad"},
                {"prompt": "___ gammal är morfar? – 89 år.", "answer": "Hur"},
                {"prompt": "___ tid har vi fikapaus? – Klockan två, tror jag.", "answer": "Vilken"},
                {"prompt": "___ studerar du italienska? – Min pojkvän kommer från Italien.", "answer": "Varför"},
                {"prompt": "___ mycket kaffe dricker du? – Inte så mycket. Bara två koppar per dag.", "answer": "Hur"},
                {"prompt": '___ heter "cat" på svenska? – "Katt".', "answer": "Vad"},
                {"prompt": "___ dags går bussen? – Fem över nio.", "answer": "Hur"},
                {"prompt": "___ gata bor du på? – Prästgatan.", "answer": "Vilken"},
                {"prompt": "___ nummer? – 12.", "answer": "Vilket"},
                {"prompt": "___ slutar vi? – Klockan fem.", "answer": "När"},
                {"prompt": "___ många barn har du? – Tre.", "answer": "Hur"},
                {"prompt": "___ bor du? – I Uppsala.", "answer": "Var"},
                {"prompt": "___ är klockan? – Tio i åtta.", "answer": "Vad"},
            ],
        },
        {
            "num": 3, "title": "Verb", "type": "fill",
            "instructions": "فعل مناسب از این‌ها رو تو جای خالیِ درست بنویس: längtar, bor, vaknar, tar, äter, pluggar, stiger, surfar, tränar, lyssnar, dricker, fikar, träffar, kommer, trivs",
            "passage": (
                "Milena ___(1)___ från Brasilien, men nu ___(2)___ hon i Stockholm och ___(3)___ "
                "filosofi på universitetet. Varje morgon ___(4)___ Milena klockan halv sju och hon "
                "___(5)___ upp direkt. Hon ___(6)___ en kopp te och ___(7)___ en banan och sedan går "
                "hon till gymmet och ___(8)___. Klockan tio ___(9)___ hon bussen till universitetet. "
                "Efter universitetet ___(10)___ hon en kompis och de ___(11)___ på ett kafé i stan. "
                "På kvällen ___(12)___ hon på internet och ___(13)___ på musik. Milena ___(14)___ bra "
                "i Sverige, men ibland ___(15)___ hon efter solen i Brasilien."
            ),
            "items": [
                {"prompt": "(1)", "answer": "kommer"}, {"prompt": "(2)", "answer": "bor"},
                {"prompt": "(3)", "answer": "pluggar"}, {"prompt": "(4)", "answer": "vaknar"},
                {"prompt": "(5)", "answer": "stiger"}, {"prompt": "(6)", "answer": "dricker"},
                {"prompt": "(7)", "answer": "äter"}, {"prompt": "(8)", "answer": "tränar"},
                {"prompt": "(9)", "answer": "tar"}, {"prompt": "(10)", "answer": "träffar"},
                {"prompt": "(11)", "answer": "fikar"}, {"prompt": "(12)", "answer": "surfar"},
                {"prompt": "(13)", "answer": "lyssnar"}, {"prompt": "(14)", "answer": "trivs"},
                {"prompt": "(15)", "answer": "längtar"},
            ],
        },
        {
            "num": 4, "title": "Substantiv: obestämd och bestämd form", "type": "fill",
            "instructions": "شکل نکره یا معرفه‌ای که کمه رو بنویس (مثال: en mössa → mössan).",
            "items": [
                {"prompt": "___ (نکره) → familjen (معرفه)", "answer": "en familj"},
                {"prompt": "ett pass (نکره) → ___ (معرفه)", "answer": "passet"},
                {"prompt": "___ (نکره) → lägenheten (معرفه)", "answer": "en lägenhet"},
                {"prompt": "en timme (نکره) → ___ (معرفه)", "answer": "timmen"},
                {"prompt": "___ (نکره) → livet (معرفه)", "answer": "ett liv"},
                {"prompt": "en sambo (نکره) → ___ (معرفه)", "answer": "sambon"},
                {"prompt": "___ (نکره) → pausen (معرفه)", "answer": "en paus"},
                {"prompt": "ett piano (نکره) → ___ (معرفه)", "answer": "pianot"},
                {"prompt": "___ (نکره) → programmet (معرفه)", "answer": "ett program"},
                {"prompt": "en gata (نکره) → ___ (معرفه)", "answer": "gatan"},
            ],
        },
        {
            "num": 5, "title": "Ordföljd: Påståenden och ja/nej-frågor", "type": "fill",
            "instructions": "از جمله‌ی خبری یه سؤال بله/خیر بساز، یا برعکس (مثال: Noi kommer från Thailand. ↔ Kommer Noi från Thailand?).",
            "items": [
                {"prompt": "Vi har fikapaus klockan tio. → سؤال بساز:", "answer": "Har vi fikapaus klockan tio?"},
                {"prompt": "Trivs Alberto i Sverige? → جمله‌ی خبری بساز:", "answer": "Alberto trivs i Sverige."},
                {"prompt": "Renate bor i Sverige nu. → سؤال بساز:", "answer": "Bor Renate i Sverige nu?"},
                {"prompt": "Jobbar Charlie på ett IT-företag? → جمله‌ی خبری بساز:",
                 "answer": "Charlie jobbar på ett IT-företag."},
                {"prompt": "Anna studerar ekonomi i Lund. → سؤال بساز:", "answer": "Studerar Anna ekonomi i Lund?"},
            ],
        },
        {
            "num": 6, "title": "Klockan", "type": "fill",
            "instructions": "ساعت رو به سوئدی بنویس (مثال: 9:00 → Klockan är nio.) — نوشتن یا ننوشتن «Klockan är» اشکالی نداره.",
            "items": [
                {"prompt": "8:10", "answer": "tio över åtta"},
                {"prompt": "9:55", "answer": "fem i tio"},
                {"prompt": "3:30", "answer": "halv fyra"},
                {"prompt": "6:15", "answer": "kvart över sex"},
                {"prompt": "10:45", "answer": "kvart i elva"},
                {"prompt": "11:05", "answer": "fem över elva"},
                {"prompt": "4:50", "answer": "tio i fem"},
                {"prompt": "2:40", "answer": "tjugo i tre"},
                {"prompt": "1:25", "answer": "fem i halv två"},
                {"prompt": "7:35", "answer": "fem över halv åtta"},
            ],
        },
        {
            "num": 7, "title": "Verb: imperativ och presens", "type": "fill",
            "instructions": "شکل امر یا زمان حال که کمه رو بنویس (مثال: Ring! ↔ ringer).",
            "items": [
                {"prompt": "läs! (امر) → ___ (حال)", "answer": "läser"},
                {"prompt": "___ (امر) → ligger (حال)", "answer": "ligg!"},
                {"prompt": "sluta! (امر) → ___ (حال)", "answer": "slutar"},
                {"prompt": "___ (امر) → är (حال)", "answer": "var!"},
                {"prompt": "ät! (امر) → ___ (حال)", "answer": "äter"},
                {"prompt": "___ (امر) → kommer (حال)", "answer": "kom!"},
                {"prompt": "skriv! (امر) → ___ (حال)", "answer": "skriver"},
                {"prompt": "___ (امر) → har (حال)", "answer": "ha!"},
                {"prompt": "gå! (امر) → ___ (حال)", "answer": "går"},
                {"prompt": "___ (امر) → spelar (حال)", "answer": "spela!"},
            ],
        },
        {
            "num": 8, "title": "Ordföljd", "type": "fill",
            "instructions": "کلمات پخش‌شده رو مرتب کن و جمله‌ی کامل بساز. اگه ترتیب تو فرق داشت ولی گرامرش درست بود، خودت بهش نمره بده.",
            "items": [
                {"prompt": "Efter ___ . (diskar / Renate / middagen)", "answer": "Efter middagen diskar Renate."},
                {"prompt": "På ___ . (te / dricker / Erik / morgonen / kopp / en)",
                 "answer": "På morgonen dricker Erik en kopp te."},
                {"prompt": "Varför ___? (Sverige / du / i / bor)", "answer": "Varför bor du i Sverige?"},
                {"prompt": "I ___ . (Albertos / sommar / kommer / mamma / Sverige / till)",
                 "answer": "I sommar kommer Albertos mamma till Sverige."},
                {"prompt": "Klockan ___ . (Alice / sig / går / tolv / lägger / och)",
                 "answer": "Klockan tolv går Alice och lägger sig."},
                {"prompt": "Anita ___ . (engelska / inte / talar)", "answer": "Anita talar inte engelska."},
                {"prompt": "Hur ___? (kursen / personer / ni / är / många / på)",
                 "answer": "Hur många personer är ni på kursen?"},
                {"prompt": "Vilken ___? (lunch / ni / äter / tid)", "answer": "Vilken tid äter ni lunch?"},
                {"prompt": "Ann-Sofie ___ . (Sverige / inte / bor / i)", "answer": "Ann-Sofie bor inte i Sverige."},
                {"prompt": "Klockan ___ . (biff och pommes frites / tolv / restaurang / i / Anna / äter / på / en / stan)",
                 "answer": "Klockan tolv äter Anna biff och pommes frites på en restaurang i stan."},
            ],
        },
        {
            "num": 9, "title": "Prepositioner", "type": "fill",
            "instructions": "حرف اضافه‌ی درست رو بنویس.",
            "passage": (
                "Carlos kommer ___(1)___ Argentina. Han är gift ___(2)___ Fredrika. Carlos är ekonom "
                "och Fredrika är journalist. Carlos jobbar ___(3)___ en bank ___(4)___ stan. Fredrika "
                "är väldigt intresserad ___(5)___ musik och just nu skriver hon en artikel ___(6)___ "
                "svensk jazz.\n\nEmilia arbetar ___(7)___ en restaurang i Uppsala. Hon jobbar ___(8)___ "
                "sex och halv två. Hon kommer hem klockan två ___(9)___ natten. Då chattar hon "
                "___(10)___ en kompis i USA. Hon berättar ___(11)___ restaurangen och jobbet där. Vid "
                "tre går hon och lägger sig och sover ___(12)___ klockan elva. Hon äter yoghurt och "
                "müsli ___(13)___ frukost. Klockan fem tar hon bussen ___(14)___ jobbet. På bussen "
                "lyssnar hon ___(15)___ musik och skriver mejl."
            ),
            "items": [
                {"prompt": "(1)", "answer": "från"}, {"prompt": "(2)", "answer": "med"},
                {"prompt": "(3)", "answer": "på"}, {"prompt": "(4)", "answer": "i"},
                {"prompt": "(5)", "answer": "av"}, {"prompt": "(6)", "answer": "om"},
                {"prompt": "(7)", "answer": "på"}, {"prompt": "(8)", "answer": "mellan"},
                {"prompt": "(9)", "answer": "på"}, {"prompt": "(10)", "answer": "med"},
                {"prompt": "(11)", "answer": "om"}, {"prompt": "(12)", "answer": "till"},
                {"prompt": "(13)", "answer": "till"}, {"prompt": "(14)", "answer": "till"},
                {"prompt": "(15)", "answer": "på"},
            ],
        },
    ],
}

FRAMSTEGSTESTER = {1: FRAMSTEGSTEST_1}
