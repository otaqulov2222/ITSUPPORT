# Web Admin Dashboard (Phase 4)

Next.js 15 (App Router) + TypeScript + Tailwind CSS. Shrift: Geist.

## Ishga tushirish

Backend `http://localhost:8000` da ishlab turishi kerak (CORS `http://localhost:3000` ga ruxsat beradi).

```powershell
cd web
copy .env.example .env.local   # NEXT_PUBLIC_API_URL ni sozlash
npm install
npm run dev                    # http://localhost:3000
```

Production:

```powershell
npm run build
npm start                      # http://localhost:3000
```

## Sozlama

| O'zgaruvchi | Default |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` |

## Kirish

`.env.example` dagi admin: `admin@pharmacy.uz` / `ChangeMeNow!123` (productionda almashtiring).

Tokenlar brauzer `localStorage` da saqlanadi (`access_token`, `refresh_token`); har bir so'rovga
`Authorization: Bearer` qo'shiladi, 401 da refresh urinib ko'riladi.

## Sahifalar

| Yo'l | Tavsif |
|---|---|
| `/login` | Email/parol bilan kirish |
| `/` | Statistika: ochiq suhbatlar, tiketlar, AI yoqilgan/to'xtatilgan |
| `/conversations` | Suhbatlar ro'yxati |
| `/conversations/[id]` | Xabarlar, javob yozish, AI to'xtatish/davom ettirish |
| `/tickets` | Tiketlar ro'yxati |

## Eslatma

Backend ro'yxat endpointlari xodim/filial nomini qaytarmaydi, shuning uchun ID qisqartirilgan
ko'rinishda ko'rsatiladi.
