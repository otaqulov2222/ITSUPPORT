# Pharmacy AI Support & Operations Platform

Telegram + Web uchun yagona backend. Server: **shu kompyuter**.

## Hozirgi holat

- **Phase 1** — Foundation ✓  
- **Phase 2** — Telegram + suhbat/ticket + WebSocket skeleti ✓  
- Docker: **Postgres (5433)** + **Redis (6379)** ✓  
- API + Bot: lokal Python (Docker image build ixtiyoriy)

## Ishga tushirish

```powershell
cd "C:\Users\Firdavs\Desktop\yordamchi Admin"
.\start-server.ps1
```

Yoki qo‘lda:

```powershell
docker compose up -d postgres redis
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
.\.venv\Scripts\python.exe -m app.bot.runner
```

## Kirish

| Narsa | Qiymat |
|-------|--------|
| API docs | http://127.0.0.1:8000/docs |
| Admin | `admin@pharmacy.uz` / `ChangeMeNow!123` |
| Telegram bot | `@vaksinamed_it_support_bot` |
| Demo xodim telefon | `+998901234567` |

### Telegram sinov

1. Botga `/start`
2. Telefon ulashish (`+998901234567` tizimda bor)
3. Matn / rasm / hujjat yuboring
4. `/ticket` yoki `/operator`

Admin API orqali suhbatlar: `GET /api/v1/conversations`  
Javob: `POST /api/v1/conversations/{id}/reply` → xodim Telegramiga ketadi  
Live: `WS /ws/admin?token=ACCESS_TOKEN`

## Testlar

```powershell
cd backend
.\.venv\Scripts\pytest.exe -q
```

## Hujjatlar

`docs/` ichida Phase 0 arxitektura va roadmap.
