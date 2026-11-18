# PHASE 0 — Project Audit

**Project:** Pharmacy AI Support & Operations Platform  
**Working directory:** `C:\Users\Firdavs\Desktop\yordamchi Admin`  
**Audit date:** 2026-11-18  
**Status:** COMPLETE — Phase 1 foundation implemented (2026-11-18)

---

## 1. Current project state

| Check | Result |
|-------|--------|
| Source code | **None** — empty directory |
| Git repository | **Not initialized** |
| Existing backend / frontend | **None** |
| Database schemas / migrations | **None** |
| Docker / CI / deploy configs | **None** |
| Secrets / `.env` | **None** |
| Documentation | **None** (created in this phase) |

**Verdict:** This is a **greenfield** project. There is no production functionality to preserve inside this workspace. All subsystems must be designed and built from scratch.

---

## 2. Nearby context (not part of this repo)

Inspected Desktop neighbors for reuse signals. They are **separate products** and must not be merged blindly.

| Path | Relevance | Notes |
|------|-----------|--------|
| `Jarvis/Jarvis/Jarvis` | Partial | Python Telegram login + voice/TTS experiments. Pattern reference only; not a pharmacy support platform. |
| `SmartOmbor-git` / `SmartOmbor-main` | Domain adjacency | Pharmacy warehouse / inventory stack (pnpm, Express, PostgreSQL, Drizzle). Useful as pharmacy domain context; **not** a support/ops AI platform. Locked agent rules — do not modify. |
| HikCentral installer on Desktop | Integration signal | Aligns with planned Hikvision / monitoring integration investigation later. |

**Reuse policy:** Steal ideas and domain vocabulary, not codebases. This platform gets its own clean architecture.

---

## 3. What must be created

### Core platform
- Backend API (REST + WebSocket)
- PostgreSQL schema + migrations
- Redis (cache, rate limits, pub/sub, queues)
- Background job workers
- Telegram bot (webhook)
- Web Admin Dashboard (React/Next.js)
- Administrator workspace (same web app, role-scoped)
- AI provider abstraction (text, vision, STT, TTS, embeddings)
- RAG / knowledge base pipeline
- Ticket engine
- Audit logging
- RBAC + branch isolation

### Separate components
- Windows Desktop Agent (device diagnostics + approved commands)
- Integration adapters (F-APTEKA, FOM, etc.) — **after** contract investigation
- Automation engine with risk tiers + kill switch

### Infrastructure
- Docker Compose (local/dev)
- Nginx reverse proxy
- Backup strategy
- Monitoring / logging
- Deployment documentation

---

## 4. What can be reused

| Asset | Decision |
|-------|----------|
| Existing code in this folder | N/A (empty) |
| Jarvis Telegram/voice snippets | Optional reference for STT/TTS flow ideas only |
| SmartOmbor domain terms (chek, smena, FOM, kassa) | Use in KB taxonomy and intent examples |
| Undocumented pharmacy software APIs | **Do not invent** — Phase 6 investigation required |

---

## 5. Security risks identified (pre-build)

Because there is no code yet, risks are **design risks** that must be prevented:

1. Building Telegram and Web as disconnected systems (explicitly forbidden).
2. Hardcoding a single AI vendor.
3. Exposing AI API keys to the frontend.
4. Autonomous high-risk automation (DB/finance/fiscal changes).
5. Cross-branch data leakage without RBAC.
6. Prompt injection via screenshots/documents.
7. Unrestricted remote shell via desktop agent.
8. Fake/mock statistics in the dashboard.
9. Destructive DB sync in production.
10. Undocumented F-APTEKA/FOM “API” assumptions.

---

## 6. Deployment infrastructure available

| Item | Status |
|------|--------|
| Local Windows 10 development machine | Available |
| Docker on this machine | **Unknown — verify in Phase 1 setup** |
| Cloud hosting / VPS | **Not configured in this repo** |
| Domain / TLS certificates | **Not configured** |
| Telegram Bot token | **Not present** (must be provided securely) |
| AI provider keys | **Not present** |

**Recommendation:** Develop with Docker Compose locally; target a Linux VPS (or managed Kubernetes later) for staging/production. Exact host to be decided with stakeholders before Phase 8.

---

## 7. Technical decisions made in Phase 0

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | Python FastAPI | Strong AI/Telegram ecosystem, async, typed, fits bot + RAG + workers |
| API style | REST + WebSocket | REST for CRUD; WebSocket for live Telegram↔Dashboard sync |
| Database | PostgreSQL 16 | Relational integrity for tickets/RBAC; pgvector for embeddings |
| Cache / queue | Redis + ARQ (or Celery) | Rate limits, pub/sub, background AI jobs |
| Frontend | Next.js (App Router) + TypeScript + Tailwind | Enterprise dashboard, SSR optional, one web app for admin + workspace |
| Telegram | python-telegram-bot (webhook) | Mature, async-friendly |
| Auth (web) | JWT access + refresh, HttpOnly cookies | Standard, works with RBAC |
| Auth (Telegram) | Phone verification + employee binding | Required by product |
| Desktop agent | Python + pywin32 / WMI | Windows diagnostics; signed installer later |
| Containers | Docker Compose | Dev parity; production base |
| Primary UX language | Uzbek Latin | Product requirement |

Open decisions (need stakeholder input before/during Phase 1–6) are listed in `INTEGRATION_PLAN.md` and the Risks section of this audit package.

---

## 8. Deliverables of Phase 0

| Document | Path |
|----------|------|
| This audit | `docs/PHASE0_AUDIT.md` |
| System architecture | `docs/SYSTEM_ARCHITECTURE.md` |
| Database design | `docs/DATABASE_DESIGN.md` |
| Security plan | `docs/SECURITY_PLAN.md` |
| Integration plan | `docs/INTEGRATION_PLAN.md` |
| Development roadmap | `docs/DEVELOPMENT_ROADMAP.md` |

---

## 9. Explicit stop point

**No application source code, migrations, or infrastructure scaffolds have been implemented beyond documentation.**

Next step requires **your approval** to begin **Phase 1 — Foundation**.
