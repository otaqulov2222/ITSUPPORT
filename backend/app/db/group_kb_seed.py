"""Real patterns from VAKSINA IT group (t.me/vaksinaITbolimi).

Manba: IT guruhidagi farmatsevt savollari + IT javoblari (qisqa, amaliy uslub).
Asosiy mavzular: kompyuter, Wi‑Fi, terminal, telefon, kamera, chek printer, AnyDesk.
"""

GROUP_KB_SEED: list[dict] = [
    {
        "title": "F-Kassa / dastur qotib qoldi (Не отвечает)",
        "category": "SOFTWARE",
        "problem": "F-Kassa yoki FOM qotib qolgan, Windows «Не отвечает» / «Закрыть программу» chiqadi",
        "symptoms": "не отвечает; not responding; закрыть программу; qotib qoldi; ko'p oyna ochiq",
        "root_cause": "Dastur osilib qolgan yoki kompyuterda ko'p dastur ochiq — bu fiskal USB emas",
        "solution": (
            "USB fleshka/MCR3500 ni qimirlatmang. «Dasturni yopish» ni bosing, "
            "keraksiz oynalarni yoping, F-Kassa ni qayta oching."
        ),
        "steps": [
            "Oynadagi «Dasturni yopish» / «Закрыть программу» tugmasini bosing",
            "Keraksiz boshqa ochiq oynalarni yoping",
            "F-Kassa / FOM ni qayta oching",
            "Yana qotsa: Ctrl+Shift+Esc → dasturni to'xtating → qayta oching",
            "Boshqa xato chiqsa — xato matnini yozing yoki yaqinroq rasm yuboring",
        ],
        "related_software": ["F-Kassa", "FOM", "Windows"],
    },
    {
        "title": "Chek chiqmayapti — printer simi (guruh uslubi)",
        "category": "PRINTING",
        "problem": "Chek printerdan chiqmayapti (Xprinter va boshqa chek printerlar)",
        "symptoms": "chek chiqmayapti; printri ishlamayapti; Xprinter; simi chiqib ketgan",
        "root_cause": "Printer yoki kompyuter tomondagi USB/sim bo'shashgan yoki chiqib ketgan",
        "solution": (
            "Avval simni ikki tomondan tekshiring: printer orqasi va kompyuter (protsessor) USB. "
            "Chiqarib qayta tiqing. Keyin chekni yana chiqaring."
        ),
        "steps": [
            "Printer orqasidagi simni tekshiring — chiqib ketgan bo'lsa qayta tiqing",
            "Kompyuter (protsessor) tomondagi USB/simni ham chiqarib qayta tiqing",
            "Printer yonikligini tekshiring",
            "Kassadan chekni qayta chiqaring",
            "Yechilmasa — ekran rasmini yuboring yoki AnyDesk ID yozing (masofadan yordam)",
        ],
        "related_software": ["Xprinter", "Printer", "FOM", "F-Kassa"],
    },
    {
        "title": "Sim qayta tiqilgach ham chek chiqmayapti",
        "category": "PRINTING",
        "problem": "Printer simini qayta tiqdim, lekin chek chiqmayapti",
        "symptoms": "simini qayta tiqdim; ishladi lekin chek chiqmayapti; qisman ishlayapti",
        "root_cause": "Ulanish tiklangan, lekin drajver/dastur/navbat yoki masofaviy sozlash kerak",
        "solution": (
            "Qaysi kompyuter ekanini aniqlang. Kerak bo'lsa AnyDesk ID yuboring — "
            "IT masofadan tekshiradi. Fiskal sozlamani o'zingiz o'zgartirmang."
        ),
        "steps": [
            "Qaysi kassa/kompyuter ekanini yozing",
            "AnyDesk dasturini oching va ID raqamini yuboring",
            "Kompyuter yonida bo'ling (masofadan ishlash uchun)",
            "IT tekshirgunicha fiskal/printer sozlamasiga tegmang",
        ],
        "related_software": ["AnyDesk", "Printer", "FOM"],
    },
    {
        "title": "HUMO terminal — seriya raqam (S/N)",
        "category": "PAYMENT",
        "problem": "HUMO terminal seriya raqami kerak / terminal muammosi",
        "symptoms": "HUMO; S/N; seriya raqam; terminal orqasi",
        "root_cause": "Identifikatsiya uchun S/N terminal orqasida/pasida yozilgan",
        "solution": "HUMO terminalning orqa (pastki) tomonida seriya raqam (S/N) yozilgan — rasmini yuboring.",
        "steps": [
            "Terminalni ehtiyotkor ag'daring",
            "Orqa/pastki tomondagi S/N yozuvini toping",
            "S/N ning aniq rasmini yuboring",
            "Terminal ekranidagi xato bo'lsa — shu oynaning ham rasmini yuboring",
        ],
        "related_software": ["HUMO", "Payment terminal"],
    },
    {
        "title": "To'lov terminali ishlamayapti (guruh)",
        "category": "PAYMENT",
        "problem": "HUMO / to'lov terminali javob bermayapti yoki to'lov o'tmayapti",
        "symptoms": "terminal ishlamayapti; HUMO; karta o'tmayapti; terminal o'chiq",
        "root_cause": "Kabel, quvvat, tarmoq yoki terminal sessiyasi",
        "solution": "Quvvat va kabelni tekshiring, terminalni o'chirib yoqing. Yechilmasa rasm + AnyDesk.",
        "steps": [
            "Terminal yonikmi — ekran yonadimi?",
            "Quvvat/USB/tarmoq kabelini chiqarib qayta tiqing",
            "Terminalni o'chirib, 10 soniya kutib yoqing",
            "Kassani qayta ochib to'lovni urinib ko'ring",
            "Yechilmasa xato rasmi va kerak bo'lsa AnyDesk ID yuboring",
        ],
        "related_software": ["HUMO", "Payment terminal", "FOM"],
    },
    {
        "title": "Wi‑Fi / internet yo'q (dorixona)",
        "category": "NETWORK",
        "problem": "Dorixonada Wi‑Fi yoki internet ishlamayapti",
        "symptoms": "wifi yo'q; internet yo'q; tarmoq yo'q; router",
        "root_cause": "Router, kabel, provayder yoki Windows ulanishi",
        "solution": "Kabel/Wi‑Fi holatini tekshiring, routerni 30 soniya o'chirib yoqing, telefon interneti bilan solishtiring.",
        "steps": [
            "Kompyuterda Wi‑Fi / kabel ulanganligini tekshiring",
            "Routerni 30 soniya o'chirib qayta yoqing",
            "Telefondagi internet bilan solishtiring — faqat kompyuterda yo'qmi?",
            "Boshqa qurilma (telefon) shu Wi‑Fi ga ulanadimi?",
            "Yechilmasa router chiroqlari rasmini yuboring",
        ],
        "related_software": ["Windows", "Router", "Wi-Fi"],
    },
    {
        "title": "Kamera / videokuzatuv ishlamayapti",
        "category": "HARDWARE",
        "problem": "Dorixona kamerasi yoki videokuzatuv ochilmayapti",
        "symptoms": "kamera ishlamayapti; video yo'q; NVR; kuzatuv",
        "root_cause": "Quvvat, tarmoq, kabеl yoki dastur ulanishi",
        "solution": "Kamera/registrator yonikligini tekshiring, tarmoqni tekshiring, xato oynasini rasmga oling.",
        "steps": [
            "Kamera va registrator (yozuv qurilmasi) yonikmi?",
            "Tarmoq/internet ishlayotganini tekshiring",
            "Dasturdagi xato oynasini rasmga oling",
            "Kabellarni qimirlatmasdan vizual tekshiring",
            "Yechilmasa IT ga rasm yuboring — sozlamani o'zingiz o'zgartirmang",
        ],
        "related_software": ["Camera", "NVR"],
    },
    {
        "title": "Telefon / aloqa muammosi (IT guruh)",
        "category": "HARDWARE",
        "problem": "Ish telefoni yoki aloqa qurilmasi ishlamayapti",
        "symptoms": "telefon ishlamayapti; qo'ng'iroq o'tmayapti; SIM",
        "root_cause": "SIM, quvvat, tarmoq yoki qurilma nosozligi",
        "solution": "Quvvat/SIM/tarmoqni tekshiring. Aniq xato bo'lsa rasm yuboring.",
        "steps": [
            "Telefon yonikmi va quvvati bormi?",
            "SIM joyida va to'g'ri tiqilganmi?",
            "Aloqa tarmog'i ko'rinadimi?",
            "Qayta yoqing",
            "Yechilmasa IT telefoniga murojaat yoki guruhga rasm yuboring",
        ],
        "related_software": ["Phone"],
    },
    {
        "title": "AnyDesk orqali masofaviy yordam",
        "category": "REMOTE",
        "problem": "IT masofadan ulanishi uchun AnyDesk kerak",
        "symptoms": "anydesk; masofadan; prinyat; ID yuboring",
        "root_cause": "Murakkab sozlash uchun masofaviy kirish",
        "solution": "AnyDesk ni oching, ID raqamini yuboring, kompyuter yonida turing, so'rovni qabul qiling.",
        "steps": [
            "AnyDesk dasturini oching (yo'q bo'lsa IT dan so'rang)",
            "Ekrandagi ID (raqam) ni aniq yozib yuboring",
            "Kompyuter yonida bo'ling",
            "IT ulanish so'rovini «Qabul qilish» bilan tasdiqlang",
            "Parol/token so'ralmasa — chatda yozmang",
        ],
        "related_software": ["AnyDesk"],
    },
    {
        "title": "Z-hisobot / Z-otchet olinmayapti (FOM)",
        "category": "POS",
        "problem": "FOM da Z-hisobot (Z-otchet) olib bo'lmayapti",
        "symptoms": "z otchet; z-hisobot; z отчет; olib bulmayapti; smena yopilmayapti",
        "root_cause": "Ochiq cheklar, printer, smena holati yoki alohida xato — birinchi navbatda USB fleshka emas",
        "solution": (
            "Avval ochiq sotuv/chek va printerni tekshiring, Z-hisobotni qayta urinib ko'ring. "
            "Xato matnini yuboring. Majburiy yopishni o'zingiz qilmang. "
            "Faqat aniq fiskallashtirish xatosi bo'lsa USB modulga o'ting."
        ),
        "steps": [
            "Yopilmagan chek yoki yarim qolgan sotuv bormi — tekshiring",
            "Chek printeri yonik/tayyor ekanini tekshiring",
            "Z-hisobot / smena yopishni qayta bosing",
            "Xato chiqsa — matnini yozing yoki yaqinroq rasm yuboring",
            "Majburiy yopishni o'zingiz qilmang — IT",
        ],
        "related_software": ["FOM", "F-Kassa"],
    },
    {
        "title": "Xprinter simi — guruh uslubi (Kabel ikki tomon)",
        "category": "PRINTING",
        "problem": "Chek chiqmayapti, Xprinter ulangan ko'rinadi",
        "symptoms": "xprinter; simi chiqib; chek chiqmay; printri",
        "root_cause": "Printer yoki kompyuter tomondagi USB/sim bo'shashgan",
        "solution": "Printer ORQASI va kompyuter (protsessor) tomondan simni chiqarib qayta tiqing. Yechilmasa AnyDesk.",
        "steps": [
            "Printer orqasidagi simni chiqarib qayta tiqing",
            "Kompyuter tomondagi USB ni ham qayta tiqing",
            "Chekni qayta chiqaring",
            "Yechilmasa qaysi kompyuter ekanini yozing / AnyDesk ID",
        ],
        "related_software": ["Xprinter", "Printer", "FOM"],
    },
    {
        "title": "Ko'p oyna ochiq — kassa sekin / qotadi",
        "category": "SOFTWARE",
        "problem": "Kassada ko'p oyna ochiq, F-Kassa sekin yoki qotadi",
        "symptoms": "ko'p oyna; sekin; qotib; не отвечает",
        "root_cause": "Resurs yetishmovchiligi — dastur osilishi",
        "solution": "Dasturni yoping, keraksiz oynalarni yoping, qayta oching. USB fleshka emas.",
        "steps": [
            "«Dasturni yopish» ni bosing",
            "Keraksiz brauzer/oynalarni yoping",
            "F-Kassa ni qayta oching",
            "Yana qotsa Ctrl+Shift+Esc dan to'xtating",
        ],
        "related_software": ["F-Kassa", "Windows"],
    },
    {
        "title": "Muammo yozganda rasm yuboring (guruh qoidasi)",
        "category": "PROCESS",
        "problem": "IT yordam uchun to'g'ri murojaat qilish",
        "symptoms": "yordam; muammo; nima qilish kerak",
        "root_cause": "Matn yetarli emas — rasm tezroq tashxis qo'yadi",
        "solution": (
            "Muammoni qisqa yozing va iloji boricha rasm yuboring "
            "(ekran xatosi, printer, terminal). Guruh: kompyuter, Wi‑Fi, terminal, telefon, kamera."
        ),
        "steps": [
            "Muammoni 1–2 jumlada yozing",
            "Ekran yoki qurilma rasmini yuboring",
            "Filial/kassa raqamini yozing (bo'lsa)",
            "Avval oddiy qadamlarni bajaring, keyin AnyDesk",
        ],
        "related_software": ["Support"],
    },
]
