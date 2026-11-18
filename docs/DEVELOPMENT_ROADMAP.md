# DEVELOPMENT ROADMAP

**Project:** Pharmacy AI Support & Operations Platform  
**Version:** 0.1 (Phase 0)  
**Rule:** No phase is “done” without its automated tests run successfully.

---

## Phase overview

| Phase | Name | Goal | Gate to next |
|-------|------|------|--------------|
| 0 | Project Audit | Architecture + docs | **Stakeholder approval** ← current stop |
| 1 | Foundation | API, DB, auth, RBAC, branches, employees, Docker | Auth + RBAC tests green |
| 2 | Telegram Support | Bot registration, chats, files, tickets, **WebSocket sync skeleton** | Bot + sync tests green |
| 3 | AI Intelligence | Providers, vision, voice, RAG, troubleshooting | AI grounding + failure tests |
| 4 | Web Dashboard | Full admin UX, live conversations, analytics | E2E admin reply → Telegram |
| 5 | Windows Agent | Diagnostics + secure commands | Agent auth + allowlist tests |
| 6 | Software Integrations | F-APTEKA/FOM investigation + adapters | Written contracts / decisions |
| 7 | Automation | Risk-tiered actions + approvals + kill switch | High-risk cannot auto-run |
| 8 | Production Readiness | Load, security, backups, monitoring, rollout | Go-live checklist signed |

---

## PHASE 0 — Project Audit _(COMPLETE)_

## PHASE 1 — Foundation _(COMPLETE — 2026-11-18)_

**Implemented**
- `backend/` FastAPI app: auth, RBAC, regions/branches/employees, audit logs
- Alembic migration `0001_phase1`
- Docker Compose (Postgres/Redis/API) — Docker localda hali o‘rnatilmagan
- Local runtime: SQLite + in-memory rate limit
- Bootstrap Super Admin seed
- Automated tests: 6/6 passed

**Note:** Telegram/Groq keys are in `.env` for later phases; Phase 1 does not call them yet.

## PHASE 2 — Telegram Support _(COMPLETE — 2026-11-18)_

**Implemented**
- Docker Postgres (`localhost:5433`) + Redis (`6379`)
- Telegram polling bot `@vaksinamed_it_support_bot`
- Phone verification → employee bind
- Conversations / messages / attachments / tickets
- Admin reply → Telegram send
- AI pause/resume + `/operator` escalation
- WebSocket hub `/ws/admin`
- Tests: Phase1+Phase2 **8 passed**

**Next:** Phase 3 — Groq AI intelligence (real troubleshooting, vision, STT, RAG)

**Deliverables**
- `docs/PHASE0_AUDIT.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DATABASE_DESIGN.md`
- `docs/SECURITY_PLAN.md`
- `docs/INTEGRATION_PLAN.md`
- `docs/DEVELOPMENT_ROADMAP.md`

**Not done in this phase:** application code, DB creation, bot tokens, deployments.

---

## PHASE 1 — Foundation

**Build**
- Repo structure (`backend/`, `web/`, `agent/` placeholder, `docker-compose.yml`)
- FastAPI app skeleton + settings/secrets loading
- PostgreSQL + Alembic migrations for org/auth core tables
- Roles/permissions seed
- Auth (register admin bootstrap, login, refresh)
- Branch / region / employee CRUD
- Audit log middleware/service
- Docker Compose: api, postgres, redis
- Basic CI: lint + unit tests

**Tests (minimum)**
1. Employee registration (API)
2. Branch identification / assignment
3. Unauthorized branch access denied
4. Audit log created on sensitive update
5. Rate limiting on auth endpoints

**Exit criteria**
- Migrated DB from empty state
- Super Admin can manage branches/employees via API
- No secrets in git

---

## PHASE 2 — Telegram Support (+ sync backbone)

**Build**
- Telegram webhook bot
- Phone verification + employee bind
- Conversations/messages/attachments persistence
- Text + photo + document + voice file intake (store only; AI later)
- Ticket creation from conversation
- Redis pub/sub + WebSocket hub skeleton
- Admin REST: list conversations, post reply → Telegram
- AI pause flag on conversation (no AI yet, but control exists)

**Tests**
4. Telegram text message persistence (simulated update)
5. Screenshot/document upload pipeline
9. Ticket creation
14. Duplicate Telegram update idempotency
15. Rate limiting per telegram user
- Admin reply path mocks Bot API send

**Exit criteria**
- Employee can register and chat
- Message appears in DB and via WebSocket to a test admin client
- Admin reply stored and send-to-Telegram invoked

---

## PHASE 3 — AI Intelligence

**Build**
- Provider interfaces + OpenAI/Anthropic/Gemini adapters (configurable)
- Conversation memory + intent classification
- Uzbek Latin / Russian response policy
- Vision analysis pipeline + PII masking best-effort
- STT for voice; optional TTS
- KB articles + document ingest + chunking + embeddings + RAG
- Troubleshooting orchestrator with confidence labels
- Usage/cost logging
- Fallback provider + timeout/retry
- Queue workers for AI jobs (Telegram ACK stays fast)

**Tests**
6. Screenshot analysis job (provider mocked)
7. Uzbek language response path
8. Russian language response path
12. Knowledge retrieval returns grounded chunk
13. AI provider failure → fallback / graceful message
- Prompt-injection fixture does not escalate privileges

**Exit criteria**
- Real provider works in staging with server-side keys
- Answers cite verified KB when available
- Unclear images produce clarification, not invention

---

## PHASE 4 — Web Dashboard

**Build**
- Next.js enterprise UI (light theme, soft blue accents)
- Modules: Overview, Branches, Employees, Conversations (live), Tickets, Assignment, Knowledge, AI Config, Monitoring (basic), Devices (readiness), Integrations (stubs), Analytics, Admins, Audit, Settings
- Human takeover + AI pause/resume UX
- Attachment preview
- Real DB statistics only
- Notifications for critical tickets

**Tests**
10. Ticket assignment
11. Ticket escalation
- E2E: Telegram inbound → dashboard visible → admin reply → Telegram outbound (staging)
19. Audit log for takeover

**Exit criteria**
- Unified Telegram + Web platform demonstrable end-to-end
- Role-scoped UI navigation
- No mock KPI numbers in production build

---

## PHASE 5 — Windows Agent

**Build**
- Device registration flow
- Heartbeat + inventory
- Collectors: OS, printers, network, DNS, disk, CPU/RAM, allowlisted services/apps
- Secure command channel
- Employee-authorized screenshot
- Admin UI for device status

**Tests**
17. Desktop agent authentication
18. Device diagnostics payload validation
- Reject unknown action codes

**Exit criteria**
- Agent on a test Windows PC reports diagnostics
- No shell escape hatch exists

---

## PHASE 6 — Software Integrations

**Build**
- Investigation docs for F-APTEKA and FOM
- Adapter scaffolding + health checks
- Staging-only implementations when contracts exist
- Explicit “not available” adapters if blocked

**Tests**
- Adapter health_check
- Permission denied for non-allowlisted action
- Staging integration tests (if environment exists)

**Exit criteria**
- Written decision per system (API / DB / Agent / deferred)
- No undocumented production DB writes

---

## PHASE 7 — Automation

**Build**
- Action catalog with risk levels
- Approval workflow
- Execution monitoring
- Emergency kill switch
- Learn-from-resolved-tickets → KB draft (admin review required)

**Tests**
16. Administrator approval required for medium/high
- Kill switch blocks execution
- HIGH risk never auto-executes

**Exit criteria**
- Full audit trail Action → Approval → Execution
- Documented runbooks for LOW/MEDIUM actions

---

## PHASE 8 — Production Readiness

**Build**
- Load testing (webhook + WS + workers)
- Security testing / dependency audit
- Backup + restore drill
- Monitoring/alerting
- Deployment docs + incident runbook
- Production rollout plan (pilot branches → all)

**Tests**
20. Concurrent user request test
- Full regression suite green
- Restore from backup verified

**Exit criteria**
- Go-live checklist signed by stakeholder
- Pilot on limited branches successful

---

## Cross-phase workstreams

| Workstream | Starts | Notes |
|------------|--------|-------|
| Documentation | Phase 0 | Update ADRs when decisions change |
| Security controls | Phase 1 | Continuous |
| Realtime sync | Phase 2 | Hardened in Phase 4 |
| UX language (UZ Latin) | Phase 2–4 | All employee-facing strings |
| Observability | Phase 4–8 | Metrics/logs/traces |

---

## Suggested repository layout (Phase 1+)

```text
yordamchi Admin/
  docs/                 # architecture & plans
  backend/              # FastAPI + bot + workers
  web/                  # Next.js dashboard
  agent/                # Windows desktop agent
  docker-compose.yml
  .env.example
  README.md
```

---

## Immediate next step after approval

1. Initialize git repository (if desired).
2. Scaffold Phase 1 backend + Docker + migrations.
3. Stakeholder inputs (partially received 2026-11-18):
   - Telegram bot token: **received** (stored in local `.env` only)
   - Preferred AI provider for staging: **Groq**
   - First pilot region/branches: **pending**
   - Whether Windows Agent is approved for POS PCs: **pending**
4. Begin Phase 1 implementation only — no Phase 3–8 scope creep.

---

## Approval checkpoint

**Stop here until explicitly approved to start Phase 1.**

Please confirm or adjust:
- [ ] Technology stack (FastAPI + Next.js + PostgreSQL + Redis)
- [ ] Unified WebSocket sync approach
- [ ] Phased roadmap order
- [ ] Open integration questions owners
- [ ] Permission to initialize the codebase
