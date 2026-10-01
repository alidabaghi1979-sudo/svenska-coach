"""
متن‌های شنیداری سوئدی — از Rivstart A1+A2 Hörförståelsetexter (Kopieringsunderlag).
هر آیتم یه تمرین شنیداری کوتاهه (مونولوگ یا دیالوگ). فصل‌ها مطابق کتابن.
کاپیتل ۱۰ (فقط لیست اسم/فرکانس) چون دیالوگ/روایت نیست حذف شده.
"""

LISTENING_ITEMS = [
    # ---------------- Kapitel 1 ----------------
    {"chapter": 1, "exercise": "2 K — معرفی خود", "lines": [
        ("", "Hej, jag heter Luisa Calderon och jag jobbar här sedan 2 år. Jag kommer från Venezuela och är 35 år. Jag talar spanska och lite italienska."),
    ]},
    {"chapter": 1, "exercise": "2 K — معرفی خود", "lines": [
        ("", "Mitt namn är Peter Andersson. Jag kommer från Gotland. Jag är ekonom och jobbar på bank. Jag arbetar med personer från Amerika så jag talar engelska varje dag. Jag talar franska också. Svenska talar jag också förstås."),
    ]},
    {"chapter": 1, "exercise": "2 K — معرفی خود", "lines": [
        ("", "Hej alla! Jag heter Nicole Duval. Jag kommer från Frankrike. Min sambo är svensk och vi pratar svenska med varandra ibland. Jag talar franska också såklart, och lite japanska och lite ryska."),
    ]},
    {"chapter": 1, "exercise": "2 K — معرفی خود", "lines": [
        ("", "Mitt namn är Jack Baxter och jag kommer från Nya Zeeland. Där talar vi engelska. Förutom engelska talar jag thailändska och tyska. Min fru är från Thailand och min mormor från Tyskland."),
    ]},
    {"chapter": 1, "exercise": "3 E — شغل و تحصیل", "lines": [
        ("Kvinna", "Pluggar du?"), ("Man", "Nej, jag jobbar. Jag är servitör på en restaurang i stan. Och du?"),
        ("Kvinnan", "Jag pluggar på Tekniska högskolan. Jag ska bli ingenjör."), ("Man", "Vad kul!"),
    ]},
    {"chapter": 1, "exercise": "3 E — شغل و تحصیل", "lines": [
        ("Kvinna", "Jag har ett nytt jobb, som webbdesigner på ett IT-företag."),
        ("Man", "Grattis! Jag jobbar kvar på restaurang Lyxlaxen som servitör. Men jag ska börja plugga till förskolelärare, tror jag."),
    ]},
    {"chapter": 1, "exercise": "3 E — شغل و تحصیل", "lines": [
        ("Flicka", "Jag ska bli frisör. Jag har börjat på frisörlinjen på gymnasiet."),
        ("Pojke", "Vad roligt. Min mamma är frisör. Men jag vill bli fotograf. Jag studerar på en fotoskola."),
    ]},
    {"chapter": 1, "exercise": "3 E — شغل و تحصیل", "lines": [
        ("Kvinna", "Min pojkvän har fått ett nytt jobb. Han är ekonom och nu har han blivit chef."),
        ("Man", "Vad skoj. Min flickvän är också ekonom. Hon jobbar på en personalavdelning. Jag är advokat. Vad gör du själv?"),
        ("Kvinnan", "Jag är kemist."),
    ]},
    {"chapter": 1, "exercise": "4 B — خانواده", "lines": [
        ("", "Jag heter Maria. Jag är gift sedan 10 år. Min man heter Peter. Vi har två barn. De är 3 och 5 år gamla."),
    ]},
    {"chapter": 1, "exercise": "4 B — خانواده", "lines": [
        ("", "Jag och min sambo är så kära. Han heter Mats och är advokat. Vi har ett barn, en son som är 2 månader. Han heter Mikael."),
    ]},
    {"chapter": 1, "exercise": "4 B — خانواده", "lines": [
        ("", "Jag heter Ingrid och bor i Göteborg. Jag är singel men jag har en dotter som heter Madicken. Jag är sjuksköterska och arbetar på ett sjukhus här i Göteborg."),
    ]},

    # ---------------- Kapitel 2 ----------------
    {"chapter": 2, "exercise": "1 H — احوال‌پرسی", "lines": [
        ("Man 1", "Hej Petter! Hur mår du?"), ("Man 2", "Bara bra, tack. Och du?"),
    ]},
    {"chapter": 2, "exercise": "1 H — احوال‌پرسی", "lines": [
        ("Kvinna 1", "Hejsan, Magdalena. Det var länge sedan! Hur mår du?"), ("Kvinna 2", "Jag mår fint! Själv då?"),
    ]},
    {"chapter": 2, "exercise": "1 H — احوال‌پرسی", "lines": [
        ("Man", "Tjena! Hur är läget Eva?"), ("Kvinna", "Så där. Jag är så förkyld."),
    ]},
    {"chapter": 2, "exercise": "1 H — احوال‌پرسی", "lines": [
        ("Kvinna 1", "Birgitta! Hur är det?"), ("Kvinna 2", "Bara bra! Jag har semester!"),
    ]},
    {"chapter": 2, "exercise": "1 H — احوال‌پرسی", "lines": [
        ("Sara", "Brian. Hur mår du?"), ("Brian", "Inte så bra. Jag är så trött!"),
    ]},
    {"chapter": 2, "exercise": "4 B — چی تو کیفته؟", "lines": [
        ("Journalist", "Hej. Får jag fråga dig en sak?"), ("Kvinna", "Javisst. Varsågod."),
        ("Journalisten", "Vad har du i väskan?"),
        ("Kvinnan", "Inte så mycket: en bussbiljett, ett läppglans, en banan, en kam, en flaska vatten och en mobiltelefon."),
        ("Journalisten", "Okej. Tack så mycket."),
    ]},
    {"chapter": 2, "exercise": "4 B — چی تو کیفته؟", "lines": [
        ("Journalist", "Ursäkta, vad har du i väskan?"),
        ("Man", "Vad jag har i väskan? Tja, jag har en mobiltelefon, ett papper, en läsk, en penna, en ordbok, pengar, och en nyckel."),
        ("Journalisten", "Okej. Tusen tack."),
    ]},
    {"chapter": 2, "exercise": "4 B — چی تو کیفته؟", "lines": [
        ("Journalist", "Hej, får jag fråga – vad har du i väskan?"),
        ("Kvinna", "I väskan? Tja, där har jag en tröja, ett par skor, en necessär, en dator, ett pass, en bok, ett paket tuggummi och en penna."),
        ("Journalisten", "Tack för det!"),
    ]},

    # ---------------- Kapitel 3 ----------------
    {"chapter": 3, "exercise": "2 B — آدرس و سن", "lines": [
        ("Man", "Bor du här i Östersund?"), ("Kvinna", "Ja, jag bor på Storgatan."),
        ("Mannen", "Jaha. Vilket nummer bor du på?"), ("Kvinnan", "64."), ("Mannen", "Då bor vi nära varandra!"),
    ]},
    {"chapter": 3, "exercise": "2 B — آدرس و سن", "lines": [
        ("Barn", "Mormor, hur gammal är du?"), ("Mormor", "Jag är 87 år."), ("Barnet", "Oj, vad gammal du är!"),
    ]},
    {"chapter": 3, "exercise": "2 B — آدرس و سن", "lines": [
        ("Kvinna", "Hur många barn har du, Mattias?"), ("Man", "Jag har 5 barn."), ("Kvinnan", "Ojojoj!"),
    ]},
    {"chapter": 3, "exercise": "2 B — آدرس و سن", "lines": [
        ("Man", "Vad har du för telefonnummer?"), ("Kvinna", "Till mobilen har jag 0792-52 98 41."),
        ("Mannen", "Okej. Jag ringer dig sen."),
    ]},
    {"chapter": 3, "exercise": "2 B — آدرس و سن", "lines": [
        ("Kvinna", "Hur många elever är ni på kursen?"), ("Man", "Vi är 14."), ("Kvinnan", "Jaha, det är inte så många."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Kvinna 1", "Vaknar du tidigt på morgonen?"), ("Kvinna 2", "Ja, jag vaknar klockan halv sex varje dag."), ("Kvinna 1", "Oj!"),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Man", "Vilken tid äter du lunch?"), ("Kvinna", "Kvart över ett."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Man 1", "När börjar vi idag?"), ("Man 2", "Tio över åtta, tror jag."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Man", "Vilken tid kommer Lena hem?"), ("Kvinna", "Kvart i tolv."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Kvinna", "När börjar teveprogrammet?"), ("Man", "Det börjar tjugo i sju."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Tonårsson", "Hur dags äter vi middag idag?"), ("Pappa", "Halv åtta."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Kvinna 1", "När slutar filmen?"), ("Kvinna 2", "Kvart över tio slutar den."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Man 1", "Hur dags ska vi ha kaffepaus?"), ("Man 2", "Vi har kaffepaus kvart i fyra idag."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Kvinna", "Vilken tid kommer posten?"), ("Man", "Klockan två, tror jag."),
    ]},
    {"chapter": 3, "exercise": "4 M — ساعت و زمان", "lines": [
        ("Man", "När går bussen?"), ("Kvinna", "Den går tjugo över sex."),
    ]},

    # ---------------- Kapitel 4 ----------------
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Grabben! Titta här. Fina paprikor! 3 för 15 kronor. REA, REA!")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Gröna gurkor. Gröna gurkor. 2 för 10. 2 för 10. Köp köp!")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Extra söta vindruvor! Bara 50 kronor kilot. Kom och smaka!")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Purjolökar. Svenska purjolökar. 14 kronor styck.")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Apelsiner! Apelsiner. Massa c-vitaminer. 2 kilo för 35 kronor. Extrapris just nu!")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Här var det bananer! Bananer från Sydamerika. 3 stycken för 16 kronor. Billigt och bra, billigt och bra!")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Äpplen! Svenska! Äpplen, 5 stycken för 23 kronor.")]},
    {"chapter": 4, "exercise": "2 B — فریاد فروشنده‌های بازار", "lines": [("", "Päron från Frankrike! Päron från Frankrike! 28 kronor kilot. Köp!")]},

    # ---------------- Kapitel 5 ----------------
    {"chapter": 5, "exercise": "2 F — برنامه‌ی هفتگی", "lines": [
        ("Max", "Vad brukar du göra en vanlig vecka, Eva?"),
        ("Eva", "Tja, vad gör jag? Det är lite olika, men på tisdagar sjunger jag i en kör. Det är kul! Jag spelar hockey också. Vi tränar på onsdagar och lördagar."),
        ("Max", "Jaha, vad roligt! Mer då?"),
        ("Eva", "Vad mer? … Jag går sällan på bio, men ibland går jag på teater. Jag gillar klassiska pjäser. Och på söndagar brukar jag träffa min pappa. Vi brukar ta en promenad och sedan fikar vi på något kafé i stan."),
        ("Max", "Det låter trevligt!"), ("Eva", "Ja, det är det."),
    ]},
    {"chapter": 5, "exercise": "2 F — برنامه‌ی هفتگی", "lines": [
        ("Sara", "Vad brukar du göra i veckorna, Adam?"),
        ("Adam", "Eh, ganska mycket faktiskt. På måndagar dansar jag salsa och på tisdagar spelar jag schack i en schackklubb."),
        ("Sara", "Kul! Något mer?"),
        ("Adam", "Oh ja. På onsdagar brukar jag gå på gym och träna och på torsdagar spelar jag poker på ett ställe i stan."),
        ("Sara", "Oj! Det var mycket!"),
        ("Adam", "Ja, men det kommer mer. På fredagar spelar jag innebandy med några kollegor och efter det brukar vi gå ut och ta en öl."),
        ("Sara", "Herregud, blir du inte trött?"),
        ("Adam", "Nej då. Allt är kul och på lördagar och söndagar gör jag inget speciellt."),
    ]},

    # ---------------- Kapitel 6 ----------------
    {"chapter": 6, "exercise": "2 D–E — خانواده‌ی من", "lines": [
        ("", "Jag har en ganska liten familj. Jag har bara en bror. Han heter Nils och är 46 år. Han är gift med Sonja som kommer från Indien. Min pappa heter Ola och är 78 år. Han bor i Frankrike. Min mamma, Alma, bor i Lund. Min pappa har inga syskon men min mamma har en syster som är 69 år. Min moster är gift med en korean och de bor i Sydkorea. Mina kusiner bor där också. Jag är ogift och har inga barn. Jag bor ensam i ett hus på landet. Det är toppen!"),
    ]},

    # ---------------- Kapitel 7 ----------------
    {"chapter": 7, "exercise": "5 G–H — قیمت‌ها", "lines": [
        ("Man", "Ursäkta, hur mycket kostar de här byxorna? Jag hittar ingen prislapp…"),
        ("Kvinna", "Jag ska kolla, ett ögonblick. De kostar 1 245 kronor."), ("Mannen", "Tack, då vet jag."),
    ]},
    {"chapter": 7, "exercise": "5 G–H — قیمت‌ها", "lines": [
        ("Kvinna 1", "Hej, vad kostar det här läppglanset?"), ("Kvinna 2", "116."), ("Kvinna 1", "Okej, jag tar det."),
    ]},
    {"chapter": 7, "exercise": "5 G–H — قیمت‌ها", "lines": [
        ("Man 1", "Hur mycket tar ni för teven här?"),
        ("Man 2", "Det är specialpris på den just nu. 2 700 den här veckan."), ("Man 1", "Det var ett bra pris!"),
    ]},
    {"chapter": 7, "exercise": "5 G–H — قیمت‌ها", "lines": [
        ("Man", "Den här slipsen var snygg. Hur mycket kostar den?"),
        ("Kvinna", "Vi ska se… Den kostar 380 kronor."), ("Man", "Okej. Jag köper den."),
    ]},

    # ---------------- Kapitel 8 ----------------
    {"chapter": 8, "exercise": "6 B — برنامه‌ریزی سفر", "lines": [
        ("Pia", "Vad vill du göra, John?"),
        ("John", "Jag vill bada i havet! Och se fin natur! Du då?"),
        ("Pia", "Jag vill också bada! Men jag skulle vilja åka till någon stad också och sitta på kaféer och shoppa lite."),
        ("John", "Okej. Kan vi göra båda, tror du?"),
        ("Pia", "Ja, vi kan åka till Malmö eller Göteborg några dagar och sedan åka till havet."),
        ("John", "Jag åker gärna till Malmö för jag vill se Öresundsbron. Och så kan vi besöka Köpenhamn en dag också."),
        ("Pia", "Vad bra! Då åker vi till Malmö och sedan till någon liten stad med en fin strand i Skåne. Det finns många fina stränder i Skåne. Ska vi hyra bil?"),
        ("John", "Nja, jag åker gärna tåg eller flyg."),
        ("Pia", "Okej, då kan vi kolla tågen."),
        ("John", "När ska vi åka?"),
        ("Pia", "Jag jobbar den 6e. Så vi kan åka den 7e eller 8e."),
        ("John", "Den 8e blir bra. Då hinner jag se lite av Stockholm först. Hur länge ska vi vara borta?"),
        ("Pia", "Ska vi åka fyra dagar till Malmö och vara vid havet i en vecka? Det blir elva dagar. Då åker vi tillbaka den 19 juli."),
        ("John", "Ja, det blir bra."),
        ("Pia", "Jag ska kolla på datorn. Oj, tåget är jättedyra! Men här är en flygbiljett till Malmö klockan sju på morgonen för 500 kronor per person."),
        ("John", "Det låter bra. Hur ska vi bo?"),
        ("Pia", "I Malmö kan vi bo på vandrarhem och sedan kan vi hyra en stuga eller tälta."),
        ("John", "Ja, vandrarhem blir bra. Och jag tältar gärna!"),
        ("Pia", "Ja, det blir roligt!"),
    ]},

    # ---------------- Kapitel 9 ----------------
    {"chapter": 9, "exercise": "1 E–F — رفت‌وآمد به سر کار", "lines": [
        ("Man", "Min flickvän tar bilen, så jag åker tunnelbana. Det tar ungefär 25 minuter. Jag brukar läsa eller lyssna på musik på tunnelbanan. Sedan tar jag buss nummer 3 som stannar precis vid jobbet."),
    ]},
    {"chapter": 9, "exercise": "1 E–F — رفت‌وآمد به سر کار", "lines": [
        ("Kvinna", "Jag jobbar på Ishotellet i Jukkasjärvi, men jag bor i Kiruna. Här i Kiruna har vi inte många bussar så jag åker alltid bil till jobbet. Det tar 10 minuter ungefär. I bilen lyssnar jag på musik och sjunger med ibland. På hotellet börjar vi dagen med att dricka kaffe och äta en bulle."),
    ]},
    {"chapter": 9, "exercise": "1 E–F — رفت‌وآمد به سر کار", "lines": [
        ("Man", "Jag har ett ganska spännande liv. Jag och min familj bor i Boston i USA, men jag jobbar i Malmö på ett svenskt företag. Jag flyger till Malmö och jobbar 10 dagar. Sedan åker jag till Boston och är ledig i fem dagar. På flyget brukar jag jobba och titta på filmer. Maten på flyget är inte så god. Från flygplatsen tar jag en taxi direkt till en restaurang och äter. Sedan går jag till jobbet."),
    ]},
    {"chapter": 9, "exercise": "1 E–F — رفت‌وآمد به سر کار", "lines": [
        ("Kvinna", "Jag bor på en ö i skärgården så jag åker båt till jobbet. Jag cyklar till båten. Ofta är jag sen och måste skynda mig. Det går bara en båt på morgonen, klockan halv sju. Båten är framme kvart över åtta. Jag börjar jobba halv nio. Det tar 10 minuter att gå till jobbet så jag hinner."),
    ]},
    {"chapter": 9, "exercise": "2 B — اعلامیه‌های حمل‌ونقل", "lines": [
        ("[På tåget]", "Och snart kommer vi in till Växjö station. Vi kommer in på spår 3. Ni som ska till Kalmar 15:17 ska ta tåget från spår 5 och för er som ska till Lund 15:34 går tåget från spår 2C."),
    ]},
    {"chapter": 9, "exercise": "2 B — اعلامیه‌های حمل‌ونقل", "lines": [
        ("[På bussen]", "Nästa hållplats är Lunden. Där kan ni byta till buss 47 och 51. Den här bussen är cirka 6 minuter försenad, men anslutningsbussarna väntar på oss."),
    ]},
    {"chapter": 9, "exercise": "2 B — اعلامیه‌های حمل‌ونقل", "lines": [
        ("[På flygbussen]", "Välkomna till bussen till Arlanda. Resan tar ungefär 40 minuter så vi är framme cirka 13:30. Vi kommer att stanna vid terminal 5 först. Sedan åker vi till terminal 4 och terminal 2."),
    ]},
    {"chapter": 9, "exercise": "2 B — اعلامیه‌های حمل‌ونقل", "lines": [
        ("[På flygplatsen]", "Sista utrop för flight nummer 117 till Malmö med avgångstid 12:50. Gå till gate 5F."),
    ]},

    # ---------------- Kapitel 11 ----------------
    {"chapter": 11, "exercise": "2 D — هجی کردن ایمیل", "lines": [
        ("Man", "Vad har du för e-postadress?"), ("Kvinna", "annika.holmgren@vackranaglar.com"),
        ("Mannen", "Vänta, kan du bokstavera det?"),
        ("Kvinnan", "a-n-n-i-k-a punkt h-o-l-m-g-r-e-n snabel-a v-a-c-k-r-a-n-a-g-l-a-r punkt com"),
        ("Mannen", "Okej, tack."),
    ]},
    {"chapter": 11, "exercise": "2 D — هجی کردن ایمیل", "lines": [
        ("Kvinna", "Har du nån e-post?"), ("Man", "Javisst. Min adress är: sebastian.viklund@skyltform.com"),
        ("Kvinnan", "En gång till?"), ("Mannen", "s-e-b-a-s-t-i-a-n punkt v-i-k-l-u-n-d at s-k-y-l-t-f-o-r-m punkt com"),
        ("Kvinnan", "Tack."),
    ]},
    {"chapter": 11, "exercise": "2 D — هجی کردن ایمیل", "lines": [
        ("Kvinna 1", "Jag ska mejla en rolig sak till dig. Vad har du för adress till jobbet?"),
        ("Kvinna 2", "mirjam.lindmark@ki.se"), ("Kvinna 1", "Vad sa du?"),
        ("Kvinna 2", "m-i-r-j-a-m punkt l-i-n-d-m-a-r-k snabel-a k-i punkt s-e"),
    ]},
    {"chapter": 11, "exercise": "2 D — هجی کردن ایمیل", "lines": [
        ("Man", "Du kanske kan mejla mig: yngve.thelander@hemlagat.se"), ("Kvinna", "En gång till."),
        ("Mannen", "y-n-g-v-e punkt t-h-e-l-a-n-d-e-r snabel-a h-e-m-l-a-g-a-t punkt s-e"),
    ]},
    {"chapter": 11, "exercise": "2 D — هجی کردن ایمیل", "lines": [
        ("Man 1", "Vill du ha min e-postadress?"), ("Man 2", "Ja, tack."), ("Man 1", "Det är tage.bolinder@mbox.se"),
        ("Man 2", "Förlåt, jag hörde inte."), ("Man 1", "t-a-g-e punkt b-o-l-i-n-d-e-r snabel-a m-b-o-x punkt s-e"),
    ]},

    # ---------------- Kapitel 12 ----------------
    {"chapter": 12, "exercise": "2 E — غذاهای مورد علاقه", "lines": [
        ("Tjej", "Jag tycker om glass och jordgubbar. Det brukar jag äta hos mormor på landet. Och på födelsedagar när man får tårta, det gillar jag. Och pannkakor. Men jag gillar verkligen inte fisk och potatis. Och inte sushi heller. Det älskar mamma och pappa, men jag tycker inte alls om det."),
    ]},
    {"chapter": 12, "exercise": "2 E — غذاهای مورد علاقه", "lines": [
        ("Kille", "Jag gillar inte grönsaker så mycket, speciellt inte sallad och tomater. Morötter är inte speciellt gott heller. Jag tycker om hamburgare. Korv är också gott."),
    ]},
    {"chapter": 12, "exercise": "2 E — غذاهای مورد علاقه", "lines": [
        ("Tjej", "Min favoritmat är köttbullar med spagetti och ketchup. Mamma tycker inte att man ska äta så mycket ketchup. Jag hatar broccoli och spenat."),
    ]},
    {"chapter": 12, "exercise": "2 E — غذاهای مورد علاقه", "lines": [
        ("Kille", "Jag brukar säga att jag är allergisk mot ost, för jag gillar inte det. Soppa är också äckligt. Jag gillar inte sparris heller. Men godis är gott."),
    ]},
    {"chapter": 12, "exercise": "2 E — غذاهای مورد علاقه", "lines": [
        ("Tjej", "Jag gillar all mat. Lax är min favoritmat. Jag gillar sill också. Något som jag inte gillar? Hmm. Bananer är inte så gott."),
    ]},

    # ---------------- Kapitel 13 ----------------
    {"chapter": 13, "exercise": "4 G–H — یه روز کاری تو هتل", "lines": [
        ("", "Jag heter Kristian och jobbar på ett hotell i Halmstad. Det är ett ganska litet hotell så jag gör en massa olika saker. Jag börjar klockan halv sju på morgonen. Då hjälper jag till med frukostserveringen. Vi har frukost mellan sju och tio. Vi serverar en stor, härlig frukost. Ibland måste jag diska också. Det tycker jag inte så mycket om. Men jag behöver inte städa i alla fall. Vid tio går jag till receptionen. Där jobbar jag till lunch. Jag svarar i telefon och tar emot bokningar. Och jag hjälper våra gäster med olika saker. Jag brukar äta lunch vid halv två i personalmatsalen. Hotellet har en fin pool och halv tre är jag ledare för ett pass vattengympa. Det är mycket populärt bland våra gäster! Mellan fyra och sex är jag ledig. Då brukar jag vila lite eller gå till stranden och bada. Ibland går jag hem och lagar en enkel middag. På kvällen, från klockan sex, arbetar jag i vår bar. Många dricker bara en öl eller ett glas vin, men ibland gör jag drinkar till våra gäster. Jag har gjort en egen drink som heter Kristians Special. Den är jättegod! Ibland har vi en man här som spelar piano i baren. Då är det fullt! Baren stänger klockan elva. Då är jag jättetrött och går direkt hem."),
    ]},

    # ---------------- Kapitel 14 ----------------
    {"chapter": 14, "exercise": "3 C — مهمونی شام", "lines": [
        ("Petra", "Välkomna. Vad roligt! Kom in. Vilken fin klänning du har!"),
        ("Mia", "Tack! Och vad fin du är!"), ("Oskar", "Vi tog med oss en flaska vin."),
        ("Ulf", "Åh, franskt vin. Vad gott! Vill ni ha en drink före maten?"),
        ("Oskar", "Nej, tack. Jag kör."), ("Mia", "Gärna för mig."),
        ("[senare]", ""),
        ("Petra", "Maten är klar. Varsågoda. Ulf, hur var det? Hur ska vi sitta?"),
        ("Ulf", "Jag sitter här med Mia, och du med Oskar där."), ("Petra", "Ta för er."),
        ("Mia", "Tack. Det ser gott ut!"), ("Petra", "Vad vill ni dricka?"),
        ("Oskar", "Ett glas vin kan jag ta, va?"), ("Mia", "Det går nog bra. Jag tar också gärna ett glas."),
        ("Oskar", "Ulf, kan du skicka saltet, tack."), ("Ulf", "Varsågod."), ("Oskar", "Tack."),
        ("Mia", "Åh, vad gott det var! Mmm. Jag måste få receptet."),
        ("Ulf", "Ja, det är ett gammalt recept från min mormor."), ("Oskar", "Mmm. Jättegott!"),
        ("Ulf", "Ta mer, om ni vill ha!"), ("Mia", "Ja, tack."), ("Oskar", "Tack. Det är bra för mig."),
        ("Petra", "Vi har glömt att skåla. Skål och välkomna! Det var så roligt att ni kunde komma!"),
        ("Alla", "Skål!"), ("[senare]", ""),
        ("Oskar", "Tack för maten! Det var så gott!"), ("Mia", "Ja, verkligen!"),
        ("Petra", "Ska vi dricka kaffet i vardagsrummet?"), ("[senare]", ""),
        ("Mia", "Vi måste börja dra oss hemåt. Tack för ikväll."), ("Oskar", "Ja, tack för allt."),
        ("Ulf", "Tack för att ni kom. Vi ses snart igen!"), ("Alla", "Hej då! Hej hej!"),
    ]},
    {"chapter": 14, "exercise": "5 D–E — نقشه‌ریزی", "lines": [
        ("Man", "Ojojoj, vad ska jag ha på mig? Jag har inga kläder."),
        ("Kvinna", "Det är lite sent att tänka på nu. Vi ska vara hos Martin och Bella om 45 minuter."),
        ("Mannen", "Ja, herregud, klockan är redan kvart över sex! Vi ska ju vara där klockan sju."),
        ("Kvinnan", "Skynda dig! Vi måste ta bussen som går halv sju."),
    ]},
    {"chapter": 14, "exercise": "5 D–E — نقشه‌ریزی", "lines": [
        ("Kvinna", "Hur ska vi komma till Göstas och Margits landställe?"),
        ("Man", "Jag har kollat upp det: Vi ska ta buss 317 från busscentralen klockan elva. Den kommer till Lillboda klockan tolv. Där ska vi byta till en annan buss – 290, tror jag det var. Den är framme i Storboda klockan halv ett. Sedan får vi gå tre kilometer."),
        ("Kvinnan", "Ja, då hinner vi till sillunchen klockan ett. Vi måste komma ihåg att köpa nubben förresten."),
    ]},
    {"chapter": 14, "exercise": "5 D–E — نقشه‌ریزی", "lines": [
        ("[på telefon]", ""),
        ("Man", "Kan ni inte komma på middag någon kväll?"), ("Kvinna", "Nja, den här veckan är det lite svårt."),
        ("Mannen", "Kanske ni vill komma hit och fika i helgen i stället?"),
        ("Kvinnan", "Ja, det kan nog funka. På lördag ska vi köpa nytt kök, men söndag kanske?"),
        ("Mannen", "Vid tretiden?"),
        ("Kvinnan", "Nja, halv fyra passar bättre, för Iris spelar tennis klockan två och vi måste hämta henne först."),
        ("Mannen", "Bra, då säger vi så."), ("Kvinnan", "Jag tar med lite fikabröd."), ("Mannen", "Kanon!"),
    ]},
    {"chapter": 14, "exercise": "5 D–E — نقشه‌ریزی", "lines": [
        ("Kvinna", "Men när börjar det egentligen?"), ("Man", "Jag minns inte … Här är inbjudan."),
        ("Kvinnan", "\"Välkomna till ceremonin i Botaniska trädgården klockan 16. Obs! Kom i tid. Middag på restaurang Lyxlaxen på Storgatan efteråt.\""),
        ("Mannen", "Då kan jag inte gå på min fotokurs den här veckan."), ("Kvinnan", "Nej, just det."),
    ]},
    {"chapter": 14, "exercise": "5 D–E — نقشه‌ریزی", "lines": [
        ("Kvinna 1", "Vad ska vi ta med oss?"), ("Kvinna 2", "Vi ska ju grilla, så vi kan väl ta med några biffar."),
        ("Kvinna 1", "Och paprika och tomat. Det är gott att grilla."),
        ("Kvinna 2", "Okej. Men oj, vi måste skynda oss! Vi ska ju ses klockan åtta, så vi måste nog gå nu."),
        ("Kvinna 1", "Ja, var ska vi handla? Här eller i stan?"), ("Kvinna 2", "I stan finns det mer att välja på."),
        ("Kvinna 1", "Okej, skynda dig!"),
    ]},

    # ---------------- Kapitel 15 ----------------
    {"chapter": 15, "exercise": "1 B — خانواده‌ی سوئدی متوسط", "lines": [
        ("", "Enligt Statistiska centralbyrån heter Medelsvensson egentligen Johansson eller Andersson i efternamn. Om medelsvensson är en kvinna heter hon Maria och hennes man heter Fredrik. Maria älskar sin man. Men ungefär hälften av alla gifta par skiljer sig. Fredrik och Maria bor med sina två barn (en pojke och en flicka) i en stad (inte på landet). Deras barn heter Oscar och Julia. Fredrik arbetar på en fabrik och hans fru jobbar i vården. Familjen äter 1,2 kilo godis i veckan och lika mycket kakor och bullar. Föräldrarna dricker 1 liter vin, 1,5 liter starköl och 13 centiliter starksprit tillsammans per vecka. De dricker mindre mjölk än tidigare, 126 liter per person och år. Grädde konsumerar de 11 liter per person och år. Fredrik är lite tjock, men det är inte Maria. De motionerar minst en gång i veckan och de röker inte. De har dator och internet hemma och barnen har egen teve och egen dator. Alla i familjen skickar 35 sms i veckan var. På fritiden läser Maria en bok och Fredrik tittar på teve. På vintern åker familjen skidor i fjällen."),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Vi ska mest vara på landet i sommar."), ("–", "Vad härligt! Hur länge då?"),
        ("–", "Jag tror det blir fyra veckor ungefär. Vecka 28 till 31."),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Vilken god kaka du har gjort. Har du receptet?"), ("–", "Ja, det är ganska många ägg i."),
        ("–", "Hur många då?"), ("–", "Sex stycken. Och mycket socker."),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Vet du vad Svenssons betalade för sitt nya hus?!"), ("–", "Nej… Hur mycket då?"),
        ("–", "5 miljoner!"), ("–", "Oj, det var dyrt…"),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Det är något som jag måste berätta för dig."), ("–", "Vad då?! Säg!"),
        ("–", "Jag har fått nytt jobb."), ("–", "Åh, vad kul! Grattis!"),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Petra kan inte komma på festen."), ("–", "Vad synd! Varför då?"),
        ("–", "Hon var dubbelbokad, sa hon."), ("–", "Okej."),
    ]},
    {"chapter": 15, "exercise": "2 B — مکالمه‌های کوتاه", "lines": [
        ("–", "Det var någon som sökte dig förut."), ("–", "Vem då?"),
        ("–", "Jag minns inte vad hon hette. Men hon ringde från Försäkringskassan."),
        ("–", "Jaha, det är om min föräldrapenning, tror jag. Jag kan ringa sedan."),
    ]},

    # ---------------- Kapitel 16 ----------------
    {"chapter": 16, "exercise": "2 I–J — مدرسه و دانشگاه", "lines": [
        ("Man", "Du Daiva. När börjar vi imorgon?"),
        ("Daiva", "Imorgon har vi inget på morgonen. Vi har en föreläsning om svensk 1900-talslitteratur klockan ett och ett seminarium om Strindberg klockan tre."),
        ("Mannen", "Just det. Har du läst ut Röda rummet?"),
        ("Daiva", "Usch. Jag har inte haft tid. Jag ska läsa den ikväll. Hoppas jag hinner."),
    ]},
    {"chapter": 16, "exercise": "2 I–J — مدرسه و دانشگاه", "lines": [
        ("Kille 1", "Vad har vi för läxor till imorgon?"),
        ("Kille 2", "Vi har massa läxor … Vi måste läsa sidan 35-37 i engelskboken och repetera orden på sidan 45. Sedan ska vi göra en presentation om Sveriges export på samhällskunskapen. Och vi ska läsa kapitel 15 i historieboken om Andra världskriget också!"),
        ("Kille 1", "Är det inte imorgon vi har prov i svenska också?"), ("Kille 2", "Nej, det är på fredag."),
        ("Kille 1", "Okej. Då hinner jag kanske plugga till det med."),
        ("Kille 2", "Förresten har du bestämt vilket program du ska läsa på gymnasiet?"),
        ("Kille 1", "Nej, inte än. Jag tror att jag ska läsa naturvetenskapligt program för jag vill bli kemist."),
        ("Kille 2", "Okej. Jag ska gå mediaprogrammet för jag vill jobba på teve."),
    ]},
    {"chapter": 16, "exercise": "2 I–J — مدرسه و دانشگاه", "lines": [
        ("Tjej 1", "Vet du vilka betyg man behöver för att komma in på juristlinjen?"),
        ("Tjej 2", "Nej, inte precis. Ganska höga tror jag."),
        ("Tjej 1", "Hmm. Jag har dåliga betyg i några ämnen. Hoppas det räcker i alla fall. Var vill du plugga sen?"),
        ("Tjej 2", "Jag vill läsa på Handelshögskolan. Man måste ju ha högsta betyg i alla ämnen för att börja där. Jag får verkligen plugga mer. Jag har så dåligt betyg i engelska."),
        ("Tjej 1", "Varför då? Du är ju så bra på engelska."), ("Tjej 2", "Jag tror inte läraren gillar mig."),
        ("Tjej 1", "Jaha, oj då. Vi får börja plugga mer i höst när vi börjar trean."),
        ("Tjej 2", "Ja, verkligen. Inga mer dataspel för mig."),
    ]},
    {"chapter": 16, "exercise": "2 I–J — مدرسه و دانشگاه", "lines": [
        ("Man", "Hej, hej. Hur har William varit idag?"), ("Kvinna", "Han har varit så glad hela dagen."),
        ("Mannen", "Vad bra. Vad har ni gjort idag?"),
        ("Kvinnan", "På förmiddagen sjöng vi och ritade och på eftermiddagen var vi ute. Vi har fotograferat höstlöv med surfplattan och sedan ska vi göra en digital fotobok om hösten i vår dator."),
        ("Mannen", "Oj, det låter avancerat."),
        ("Kvinnan", "Ja, för oss lärare. Barnen har inga problem med att använda datorer. William blir nog en riktig IT-expert när han blir stor."),
        ("Mannen", "Haha, ja vi får väl se."),
    ]},

    # ---------------- Kapitel 17 ----------------
    {"chapter": 17, "exercise": "2 D — مسکن", "lines": [
        ("", "Roine berättar hur han och hans kollegor bor: Igår, när vi hade fikapaus, satt mina kollegor och jag och pratade om bostäder. Jag berättade att min sambo och jag precis har flyttat till en ny lägenhet. Förut bodde vi i ett litet hus, men vi ville hellre bo i stan. Så vi sålde vårt hus och köpte en jättefin bostadsrätt mitt i stan. Det är en ganska stor lägenhet, en fyra. Det är bra att ha ett extrarum om vi får barn någon gång i framtiden. Vår administratör, Lena, bor med sin man i en villa utanför stan. De har en stor trädgård och nästa år ska de bygga en pool. Lenas man älskar att arbeta i trädgården. Det är tur, för Lena hatar trädgårdsarbete. Olle, som jobbar extra på kvällarna, pluggar ekonomi på universitetet. Han bor i ett studentrum nu, men han måste flytta tillbaka till sina föräldrar. Han vill inte, men han säger att det är så dyrt att bo ensam. Stackars Pernilla letar fortfarande efter en egen lägenhet. Hon har bott i andra hand länge nu. Hon berättade att hon har bott i fem olika lägenheter på två år så hon är jättetrött på att flytta runt. När hon har lite mer pengar ska hon köpa en etta utanför stan. Sedan har vi min chef, Cecilia. Hon bor med sin sambo här i stan, men de vill flytta till en husbåt! Båda älskar vatten, men de vill inte bo på landet. Och ingen av dem tycker om trädgårdsarbete. Det finns en marina fem minuter från stan. Där kan man köpa husbåt. Cecilia och hennes sambo tittade på en i lördags. Det är faktiskt billigare att köpa husbåt än villa."),
    ]},

    # ---------------- Kapitel 18 ----------------
    {"chapter": 18, "exercise": "2 E–F — تماس خودکار", "lines": [
        ("Automatisk röst", "Välkommen till MobilfixNu."), ("Man", "Ja, hej, jag…"),
        ("Röst", "För bästa service, var vänlig knappa in ditt mobilnummer. Avsluta med fyrkant."),
        ("Man", "Jaha … 0-7-0-9-2-8-0-5-6-3. Och så fyrkant. Så."),
        ("Röst", "Var vänlig säg vad ditt ärende gäller."), ("Man", "Eehhh, jag vill byta telefonnummer."),
        ("Röst", "Gäller det \"fakturafrågor\"?"), ("Man", "Nej. Jag vill ha NYTT TELEFONNUMMER."),
        ("Röst", "Gäller det \"faktureringsadress\"?"), ("Man", "Jag sa just att jag vill ha NYTT TELEFONNUMMER!"),
        ("Röst", "Kan du upprepa, tack?"),
        ("Man", "Men, herregud, JAG VILL HA ETT NYTT TELEFONNUMMER. Hur svårt kan det vara??"),
        ("Röst", "Du kommer nu att få höra fyra alternativ. För fakturafrågor, tryck 1. För information om våra kampanjer, tryck 2. För övriga frågor, tryck 3. För personlig service, tryck 4. Avsluta med fyrkant."),
        ("Man", "Det får bli personlig service."),
        ("Röst", "Just nu är det många som ringer till oss. Ditt samtal är placerat i kö. Du har plats nummer 37 i kön. Tack för att du väntar."),
        ("Man", "Men HALLÅ, Jag har inte tid att vänta!!"),
        ("Röst", "Just nu är det många som ringer till oss. Ditt samtal är placerat i kö. Du har plats nummer 37 i kön. Tack för att du väntar."),
        ("Man", "Nej, du. Nu väntar jag inte mer. ADJÖ!"),
    ]},
    {"chapter": 18, "exercise": "4 B — پیام تلفنی", "lines": [
        ("[i telefon]", ""),
        ("Man", "Dentalprodukter AB, Nils Petterson."), ("Kvinna", "Hej. Mitt namn är Siv Olofsson. Jag söker Bengt Lindén."),
        ("Mannen", "Ett ögonblick."), ("Mannen", "Bengt sitter i ett möte just nu."),
        ("Kvinnan", "Kan jag tala med Anna Svensson i stället?"),
        ("Mannen", "Tyvärr. Hon sitter i telefon. Kan jag ta ett meddelande?"),
        ("Kvinnan", "Ja, du kan be Bengt att ringa Siv Olofsson på Tandkliniken AB. Det gäller en leverans som inte har kommit. Det är bråttom."),
        ("Mannen", "Ja, det ska jag hälsa. Har han ditt nummer?"),
        ("Kvinnan", "Ja, det har han, men ta det i alla fall. Det är 517 13 12."),
        ("Mannen", "517 13 12?"), ("Kvinnan", "Just det. Tack och hej."), ("Mannen", "Hej då."),
    ]},
    {"chapter": 18, "exercise": "4 C — پیام تلفنی", "lines": [
        ("Kvinna", "KemAB, god morgon. Det här är Lisa Smith."),
        ("Man", "Mitt namn är Ulf Lundin. Jag söker Annette Stenberg."),
        ("Kvinnan", "Hon sitter i möte just nu. Kan jag hälsa henne något?"),
        ("Mannen", "Ja, hälsa henne att hon måste mejla mig dokumenten om det nya huset. Min e-postadress är ulf.lundin at experterna.se"),
        ("Kvinnan", "ulf.lundin snabel-a experterna.se. Jag ska hälsa henne det. Är det bråttom?"),
        ("Mannen", "Ja, jag behöver dokumenten före klockan fyra."), ("Kvinnan", "Före klockan fyra. Jag ska framföra det."),
        ("Mannen", "Tack för det."), ("Kvinnan", "Tack. Hej då."), ("Mannen", "Hej då."),
    ]},
    {"chapter": 18, "exercise": "4 C — پیام تلفنی", "lines": [
        ("Kvinna", "Linguina AB, det är Petra Magnusson."),
        ("Man", "Hej, det här är Magnus Svensson på kundservice. Jag försöker få tag på Erik Sundkvist."),
        ("Kvinnan", "Erik? Han är ute på lunch just nu. Kan jag hälsa något?"),
        ("Mannen", "Ja, kan du be att han ringer mig, före klockan två. Vi har problem med en kund."),
        ("Kvinnan", "Okej. Före klockan två. Har han ditt nummer?"),
        ("Mannen", "Jag tror det, men det är bäst att du tar det. 073 82 15."),
        ("Kvinnan", "073 82 15. Jag ska hälsa honom det."), ("Mannen", "Vad bra! Tusen tack!"),
    ]},

    # ---------------- Kapitel 19 ----------------
    {"chapter": 19, "exercise": "3 B — مارتین مریضه", "lines": [
        ("", "Martin vaknar på morgonen och känner sig dålig. Han har ont i huvudet och i halsen. Förmodligen har han hostat mycket under natten. Han måste köpa hostmedicin idag. Kanske har han feber också? Bäst att kolla."),
        ("Martin", "Madeleine, snälla, kan du hämta febertermometern i badrummet?"),
        ("Madeleine", "Kan du inte hämta den själv? Så sjuk är du väl inte?"),
        ("Martin", "Jo, det är jag faktiskt. Jag kan inte komma upp ur sängen. Jag tror att jag har influensa."),
        ("", "Martin tänker att symptomen skulle kunna vara typiska för hjärntumör också, eller meningit. Men det säger han inte till Madeleine. Han ska titta i boken Hemmadoktorn sedan."),
        ("Madeleine", "Varsågod, här är termometern."), ("Martin", "Tack."),
        ("Madeleine", "Ska du inte gå och äta frukost nu?"), ("Martin", "Nej, jag väntar och ser om du har feber."),
        ("Madeleine", "Nå?"), ("Martin", "36,7."), ("Madeleine", "Vad bra! Ingen feber."),
        ("Martin", "Konstigt. Jag känner mig jättedålig så jag stannar i sängen idag."),
        ("", "När Madde har gått tar Martin fram boken Hemmadoktorn. Han läser om olika sjukdomar och tänker att det är bäst att gå till doktorn direkt. Förra veckan sa doktorn att han inte behövde gå till doktorn så ofta. Han hade sagt att Martin var 100 % frisk. Men det var förra veckan. Den här gången är Martin helt säker på att han har en mycket allvarlig sjukdom."),
    ]},

    # ---------------- Kapitel 20 ----------------
    {"chapter": 20, "exercise": "2 B — اخبار: تظاهرات رستوران", "lines": [
        ("", "Klockan är 18. Här är Nyheterna. Rubrikerna i dagens sändning: Restaurang ska rivas, Skandal på Odenbanken, Vin bra för hälsan, Ekonominyheter, Vädret."),
        ("", "Igår demonstrerade cirka 400 personer i Småstad mot att restaurang Monopol i centrum ska rivas. Byggnaden är från 1870 och enligt kulturhistoriker mycket intressant. Här har många kända personer, både från Sverige och resten av världen ätit, druckit och roat sig. Men nu verkar det som om den perioden är slut. Företaget som äger restaurangen, Invest AB, säger till nyheterna att restaurangen måste renoveras. Det blir för dyrt så i stället väljer man att riva och bygga nytt. En namninsamling har startat för att rädda den gamla restaurangen. Men Ulf Berg på Invest AB säger att de inte kommer att ändra sig:"),
        ("Ulf Berg", "Restaurangen är för gammal och omodern. Det kostar för mycket att renovera helt enkelt."),
        ("", "Demonstranterna meddelar att de inte kommer att ge upp."),
    ]},
    {"chapter": 20, "exercise": "2 B — اخبار: رسوایی بانکی", "lines": [
        ("", "Kunderna på Odenbanken är oroliga. En person som jobbar på banken har flyttat pengar från kundernas konton till sitt eget, i Schweiz. Detta har pågått under flera år. Mannen förde över små belopp (10 eller 20 kronor) från varje konto för att ingen skulle märka något. Totalt har han tagit 2 miljoner kronor. Han riskerar upp till 5 års fängelse. Nyheterna har talat med en av kunderna:"),
        ("Kund", "Ja, från mitt konto verkar han inte ha tagit någonting, men man vet ju aldrig. Man blir orolig i alla fall. Kanske är det bättre att ha pengarna i madrassen."),
    ]},
    {"chapter": 20, "exercise": "2 B — اخبار: شراب و سلامتی", "lines": [
        ("", "Nu är det bevisat. Ett glas vin om dagen är bra för hjärtat. Enligt en stor internationell studie löper vinkonsumenter 20 % mindre risk att drabbas av hjärtsjukdomar."),
        ("", "Eva Nilsson på Sahlgrenska sjukhuset i Göteborg:"),
        ("Eva Nilsson", "Vi har undersökt 20 000 personer under en 10-årsperiod. Vin skyddar men vi vet inte varför. Kanske beror det på antioxidanterna i vinet."),
        ("Reporter", "Kan ni rekommendera folk att dricka vin?"),
        ("Eva Nilsson", "Nej, faktiskt inte. Vin har så många negativa effekter, så att någon generell rekommendation vill vi inte gå ut med."),
    ]},
    {"chapter": 20, "exercise": "2 C — اخبار اقتصادی", "lines": [
        ("", "Och så ekonominyheter: igår stängde börsen på upp 1,3 procent. Euron står i 8,97. Dollarn i 7,15. Den långa räntan ligger på 3,3 procent. Arbetslösheten ligger på 6,5 mot 4,3 procent samma tid förra året och inflationen är på 1,42 procent vilket är något högre än förra kvartalet."),
    ]},
    {"chapter": 20, "exercise": "2 D — پیش‌بینی هوا", "lines": [
        ("", "Och nu till vädret med Åsa Persson. Ikväll kommer ett regnväder in över Götaland. Regnet sprider sig upp över landet och i Svealand övergår det i snö. I Norrland blir det klart."),
        ("", "Imorgon klart väder i Götaland och Svealand. Södra Norrland får snö och Norra Norrland får mulet men ingen snö. Temperaturen i Götaland 3 till 7 plusgrader. I Svealand och Norrland mellan 0 och minus 10 grader."),
    ]},
]
