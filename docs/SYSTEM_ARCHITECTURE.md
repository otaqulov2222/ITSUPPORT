# SYSTEM ARCHITECTURE

**Project:** Pharmacy AI Support & Operations Platform  
**Version:** 0.1 (Phase 0)  
**Status:** Proposed — awaiting approval

---

## 1. Architectural principles

1. **One platform, two faces** — Telegram (employees) and Web Dashboard (admins) share one backend, one database, one AI engine, one ticket system.
2. **Real-time sync** — Telegram events appear on the dashboard immediately; admin replies reach Telegram.
3. **Provider-independent AI** — no hardcoded vendor lock-in.
4. **Least privilege** — RBAC + branch isolation + risk-tiered automation.
5. **Async by default** — AI, STT, vision, and RAG run via queues; Telegram never blocks on a single long LLM call.
6. **No fake production data** — dashboard metrics come from the database.
7. **No undocumented pharmacy APIs** — adapters only after investigation and contracts.
8. **Security first** — untrusted uploads, prompt-injection resistance, audit everything sensitive.

---

## 2. High-level system context

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Pharmacy Employee│     │ IT / Network Admin│     │ Super Admin      │
│ (Telegram)       │     │ (Web Workspace)   │     │ (Web Dashboard)  │
└────────┬─────────┘     └────────┬──────────┘     └────────┬─────────┘
         │                        │                         │
         │ Bot API                │ HTTPS + WSS             │ HTTPS + WSS
         ▼                        ▼                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Edge (Nginx + TLS)                             │
└────────────────────────────┬───────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Telegram Webhook│ │ REST API        │ │ WebSocket Hub   │
│ Handler         │ │ (FastAPI)       │ │ (live sync)     │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │     Application Core         │
              │  Auth · RBAC · Tickets ·     │
              │  Conversations · KB · Audit  │
              └──────────────┬───────────────┘
                             │
     ┌───────────────┬───────┼───────┬───────────────┐
     ▼               ▼       ▼       ▼               ▼
┌─────────┐   ┌─────────┐ ┌─────┐ ┌─────────┐  ┌──────────┐
│PostgreSQL│   │ Redis   │ │Queue│ │ Object  │  │ AI Gateway│
│+ pgvector│   │cache/   │ │Workers│ Storage│  │(providers)│
│         │   │pubsub   │ │     │ │(files)  │  │          │
└─────────┘   └─────────┘ └─────┘ └─────────┘  └──────────┘
                                                   │
                    ┌──────────────────────────────┼──────────┐
                    ▼                              ▼          ▼
           ┌────────────────┐            ┌─────────────┐ ┌────────┐
           │ Windows Agents │            │ Integration │ │External│
           │ (pharmacy PCs) │            │ Adapters    │ │AI APIs │
           └────────────────┘            └─────────────┘ └────────┘
```

---

## 3. Technology stack (recommended)

| Layer | Technology | Role |
|-------|------------|------|
| Backend API | Python 3.12 + FastAPI | REST, WebSocket, DI, OpenAPI |
| ORM / migrations | SQLAlchemy 2.x + Alembic | Schema, migrations |
| DB | PostgreSQL 16 + pgvector | Relational data + embeddings |
| Cache / broker | Redis 7 | Sessions cache, rate limit, pub/sub, queue |
| Jobs | ARQ (preferred) or Celery | AI jobs, STT, embeddings, SLA checks |
| Telegram | python-telegram-bot (v21+) | Webhook bot |
| Frontend | Next.js 15 + TypeScript + Tailwind | Admin dashboard + workspace |
| UI state / realtime | TanStack Query + native WebSocket client | Live conversations/tickets |
| Auth | JWT + refresh tokens (HttpOnly cookie) | Web sessions |
| File storage | Local volume (dev) → S3-compatible (prod) | Screenshots, docs, voice |
| Reverse proxy | Nginx | TLS, routing, static |
| Containers | Docker + Compose | Dev/staging/prod baseline |
| Desktop agent | Python 3.12 + Windows service | Diagnostics + approved actions |
| Observability | structured JSON logs + Prometheus metrics (Phase 8) | Ops |

---

## 4. Backend module boundaries

```
backend/
  app/
    api/                 # HTTP routers (auth, branches, tickets, ...)
    ws/                  # WebSocket endpoints
    bot/                 # Telegram webhook + handlers
    core/                # config, security, logging, errors
    domain/              # entities / enums (pure)
    services/            # business logic
      conversation/
      ticket/
      knowledge/
      automation/
      device/
      analytics/
    ai/                  # provider interfaces + orchestrator
      providers/
      rag/
      vision/
      voice/
      prompts/
    integrations/        # F-APTEKA, FOM, ... adapters (stubs until Phase 6)
    workers/             # background jobs
    db/                  # models, session, repositories
  alembic/
  tests/
```

**Rule:** Bot handlers and API routers stay thin. Business rules live in `services/`. AI providers never talk to the database directly.

---

## 5. Unified conversation bus (Telegram ↔ Web)

### 5.1 Single source of truth

All messages (employee Telegram, AI replies, admin replies) are stored in:

- `conversations`
- `messages`
- `attachments`

Telegram message IDs are stored for outbound mapping; web admins never need Telegram internals.

### 5.2 Real-time flow

**Inbound (Telegram → Dashboard):**

1. Telegram webhook receives update.
2. Persist message + attachment metadata.
3. Publish event on Redis channel `conversation:{id}`.
4. WebSocket hub fans out to subscribed admin clients.
5. Enqueue AI processing job (unless AI paused / human takeover).

**Outbound (Dashboard → Telegram):**

1. Admin sends reply via REST.
2. Persist message (`sender_type=ADMIN`).
3. Bot service sends Telegram message to employee chat.
4. Publish same event to WebSocket subscribers (including other admins).

**AI pause / takeover:**

- `conversations.ai_enabled` boolean.
- When `false`, workers skip auto-reply; admins own the thread.
- Audit log on every pause/resume/takeover.

### 5.3 Idempotency

- Telegram `update_id` uniqueness.
- Client-generated `idempotency_key` on admin sends.
- Job IDs for AI tasks to avoid duplicate replies.

---

## 6. AI architecture

### 6.1 Provider interfaces

```
TextGenerator
VisionAnalyzer
SpeechToText
TextToSpeech
EmbeddingProvider
```

Each provider adapter implements one or more interfaces (Groq first for staging; also OpenAI, Anthropic, Gemini, local/compatible).

### 6.2 Orchestrator pipeline (per employee message)

```
Normalize language (uz/ru/en)
  → Load conversation memory (last N + summary)
  → Classify intent / category / severity
  → If image: vision analysis (with PII masking policy)
  → If voice: STT → treat as text
  → RAG retrieve verified KB chunks
  → Build grounded prompt (cite KB; mark confidence)
  → Generate response + suggested ticket fields
  → Persist AI message + usage log
  → Optionally create/update ticket
  → Publish realtime event
```

### 6.3 Grounding rules

Every technical answer must label confidence:

- **Verified instruction** — from approved KB article
- **Likely diagnosis** — pattern match + incomplete evidence
- **Unverified assumption** — must ask clarifying questions

Never invent company policy, error codes, or “problem solved” without confirmation.

### 6.4 Prompt injection defenses

- Treat uploads as untrusted data, not instructions.
- Separate system policy from user/content channels.
- Strip / ignore “ignore previous instructions” patterns in OCR text.
- Tool/automation calls require server-side permission checks, never model trust alone.

---

## 7. Telegram architecture

| Concern | Design |
|---------|--------|
| Mode | Webhook only in staging/prod; polling allowed for local dev |
| Entry | `/start` → registration / phone share |
| Auth | Phone verification → bind `telegram_accounts` to `employees` |
| UX | Natural language; minimal commands (`/help`, `/ticket`, `/operator`) |
| Media | Photos, documents, voice downloaded to object storage |
| Context | Conversation session per employee+branch |
| Escalation | `/operator` or AI escalation → ticket + notify admins via WS + optional Telegram admin alerts |
| Languages | Primary Uzbek Latin; auto-detect Russian/English |

Registration gates: unverified users cannot open tickets for arbitrary branches.

---

## 8. Web Admin Dashboard architecture

Single Next.js app with role-based route groups:

| Area | Audience | Key modules |
|------|----------|-------------|
| `/dashboard` | All admins | Overview KPIs (live DB) |
| `/branches`, `/employees` | Regional+ | Org management |
| `/conversations` | Support/IT | Live Telegram threads, takeover, AI pause |
| `/tickets` | Support/IT | Queue, assign, SLA, resolve |
| `/knowledge` | IT/Admins | Articles, document upload, RAG reindex |
| `/devices` | Network Admin | Agent fleet, diagnostics, commands |
| `/integrations` | Super Admin | Adapter configs (no secrets in UI plaintext after save) |
| `/ai` | Super Admin | Provider selection, models, usage/cost |
| `/analytics` | Managers+ | Reports |
| `/admins`, `/audit`, `/settings` | Super Admin / Auditor | Access & compliance |

Realtime: authenticated WebSocket `/ws/admin` with channel subscriptions scoped by RBAC (region/branch).

---

## 9. Windows Agent architecture

```
Pharmacy PC
  └── Pharmacy AI Desktop Agent (Windows Service)
        ├── Device credentials (mTLS or device JWT)
        ├── Heartbeat + inventory
        ├── Diagnostic collectors (OS, printers, network, disk, services)
        ├── Approved command executor (allowlist only)
        └── Secure uplink to API `/agent/*`
```

**Hard constraints:**

- No unrestricted remote shell.
- No silent screen capture — employee authorization required for screenshots.
- No password / payment credential collection.
- High-risk actions never autonomous; require admin approval records.

---

## 10. Safe automation engine

| Risk | Examples | Gate |
|------|----------|------|
| LOW | Printer status, ping, disk space, service status, collect logs | Auto if policy allows |
| MEDIUM | Restart approved service/app, clear approved cache | Admin or elevated policy + audit |
| HIGH | DB writes, fiscal, prices, stock, permissions, network core | Explicit multi-step approval + kill-switch check; never AI-autonomous |

Global **kill switch** (`system_settings.automation_enabled`) disables all remote execution immediately.

---

## 11. Scalability model

| Component | Scale strategy |
|-----------|----------------|
| API | Horizontal replicas behind Nginx |
| WebSocket | Sticky sessions or Redis-backed hub |
| Workers | Independent replicas per queue type (ai, stt, rag, notifications) |
| PostgreSQL | Vertical first; read replicas later for analytics |
| Redis | Managed or replicated |
| Object storage | S3-compatible for multi-instance file safety |
| Telegram webhook | Fast ACK + enqueue; heavy work in workers |

Target path: 150 branches → 1,000+ without redesigning module boundaries.

---

## 12. Environment topology

```
dev:      docker-compose (api, worker, bot, web, postgres, redis, minio)
staging:  single VPS or small cluster + staging Telegram bot
prod:     multi-service + backups + monitoring + separate secrets
```

---

## 13. Architectural decision records (initial)

| ID | Decision | Status |
|----|----------|--------|
| ADR-001 | FastAPI + Next.js + PostgreSQL + Redis | Proposed |
| ADR-002 | Unified conversation store + Redis pub/sub + WebSocket | Proposed |
| ADR-003 | pgvector for RAG (keep stack simple) | Proposed |
| ADR-004 | ARQ on Redis for job queue | Proposed |
| ADR-005 | Desktop agent as separate repo/module under `/agent` | Proposed |
| ADR-006 | Integration adapters behind interfaces; no assumed APIs | Proposed |
| ADR-007 | Uzbek Latin primary in all employee-facing copy | Accepted (product) |
| ADR-008 | Groq as first staging text LLM provider | Accepted (stakeholder) |

---

## 14. Non-goals (Phase 0–2)

- Replacing F-APTEKA / FOM themselves
- Autonomous financial or fiscal operations
- Public multi-tenant SaaS for unrelated companies (single pharmacy network first; schema remains tenant-ready)
- Building a mobile native app (Telegram covers field UX initially)
