# INTEGRATION PLAN

**Project:** Pharmacy AI Support & Operations Platform  
**Version:** 0.1 (Phase 0)  
**Status:** Investigation-first — no assumed undocumented APIs

---

## 1. Integration principles

1. **Do not invent APIs.** If a vendor interface is undocumented, treat it as unavailable until a contract exists.
2. **Adapter pattern.** Each external system has its own module with auth, config, health checks, errors, logging, permissions, tests.
3. **Prefer read-only diagnostics first.** Write operations require explicit approval and contracts.
4. **Never modify production pharmacy DBs** without an approved integration agreement.
5. **Fail safe.** Integration outage must not crash Telegram or ticket flows.
6. **Branch-aware config.** Credentials and endpoints may differ per branch or region.

---

## 2. Adapter interface (standard)

Every adapter implements:

```text
connect() / disconnect()
health_check() -> HealthResult
authenticate()
execute(action, context) -> Result   # only allowlisted actions
map_error(exception) -> DomainError
```

Cross-cutting:

- Structured logs with `integration_code`, `branch_id`, correlation id
- Timeout + retry with jitter (idempotent reads only)
- Secret references (not inline secrets)
- Permission gate before each action
- Contract tests against staging, never against prod blindly

---

## 3. Target systems

### 3.1 F-APTEKA

| Item | Status |
|------|--------|
| Official public API | **Unknown — must investigate** |
| Likely integration paths | Vendor API (if any), DB views (contracted), Windows UI automation (**discouraged**), Desktop Agent log/process checks |
| Phase | Phase 6 |
| Allowed before contract | Process presence, log tail (approved paths), user-guided troubleshooting via KB |
| Forbidden without contract | Direct sales/stock/price DB writes |

**Open questions**
- Is there a vendor-supported API or middleware?
- What is the supported DB engine and access policy?
- Can staging instances be provided per region?

### 3.2 FOM

| Item | Status |
|------|--------|
| Meaning in network | Appears in employee language as software/error source (“FOM xatolik”) |
| Official API | **Unknown — must investigate** |
| Phase | Phase 6 |
| Interim support | Symptom → KB article mapping; screenshot OCR; ticket escalation |

**Open questions**
- Exact product name/vendor and version matrix across branches
- Error code catalog availability
- Whether FOM is fiscal middleware, POS module, or separate app

### 3.3 Windows / POS workstation

| Path | Method |
|------|--------|
| OS info, disk, CPU/RAM | Desktop Agent (WMI/WinAPI) |
| Printers | Agent printer enumeration + status |
| Services | Allowlisted service status/restart |
| App running? | Process allowlist |
| Screenshots | Explicit employee consent only |

### 3.4 Receipt / fiscal printers

- Detect via agent (queue status, offline, paper out) when OS exposes it.
- Do not flash firmware or change fiscal config autonomously.
- KB-driven manual steps for fiscal legal settings.

### 3.5 Barcode scanners / payment terminals

- Mostly guided troubleshooting (USB, drivers, COM ports).
- Payment terminals: **no** credential harvesting; escalate to human for merchant/bank issues.

### 3.6 Network / routers / internet

- Agent: gateway ping, DNS resolve, HTTP connectivity checks.
- Router admin changes: high risk; human only unless approved script exists.

### 3.7 Databases (pharmacy)

- Access only with read-only credentials and contract.
- Writes classified HIGH risk; dual approval + kill switch.
- Prefer vendor APIs over raw SQL.

### 3.8 Hikvision / monitoring

- Desktop evidence of HikCentral installer exists on stakeholder machine — suggests possible CCTV/ops monitoring use.
- Integration only via official Hikvision/HikCentral APIs after credential and scope definition.
- Not required for MVP support chat/tickets.

### 3.9 Telegram

- First-class channel (Phase 2).
- Bot API webhook + file download.
- Admin outbound replies use Bot API send methods.
- Webhook secret token validation mandatory.

### 3.10 AI providers

- OpenAI / Anthropic / Gemini / compatible endpoints via provider adapters.
- Separate configs for text, vision, STT, TTS, embeddings.
- Fallback chain when primary fails.

---

## 4. Alternative integration patterns (when no API)

| Pattern | Use when | Risk |
|---------|----------|------|
| Desktop Agent diagnostics | Local Windows truth needed | Medium (must allowlist) |
| Approved log readers | Vendor logs on disk | Low–Medium |
| Documented DB read views | Vendor provides views | Medium |
| Remote support tool handoff | Human needed | Process risk |
| UI automation | Last resort | High — avoid |

---

## 5. Unified Telegram + Web sync (internal integration)

This is an **internal** integration requirement, not a third-party API:

| Event | Producer | Consumers |
|-------|----------|-----------|
| Employee message | Telegram webhook | DB, AI worker, WebSocket admins |
| AI reply | AI worker | DB, Telegram send, WebSocket |
| Admin reply | Web REST | DB, Telegram send, WebSocket |
| AI pause/resume | Web REST | DB, workers, WebSocket |
| Ticket status change | Ticket service | DB, notifications, WebSocket, optional Telegram notify |

Transport: Redis pub/sub + WebSocket hub.  
Consistency: DB commit first, then publish (outbox pattern recommended by Phase 2/3).

---

## 6. Phase 6 investigation checklist

For each of F-APTEKA and FOM:

1. Collect exact product versions used in ≥3 sample branches.
2. Ask vendor/IT for supported integration options in writing.
3. Identify auth mechanisms and rate limits.
4. Obtain staging environment.
5. Document allowlisted operations (read vs write).
6. Implement adapter stub → staging adapter → production adapter.
7. Add health checks and audit hooks.
8. Write integration tests against staging only.

**Exit criteria:** written `docs/integrations/F_APTEKA.md` and `docs/integrations/FOM.md` with decision: API / Agent / DB / Not feasible.

---

## 7. Unresolved integration questions (need stakeholders)

1. Who owns F-APTEKA / FOM vendor relationships and can request API access?
2. Are pharmacy DB credentials shareable to a central platform under policy?
3. Is a Windows Agent install approved on all POS machines?
4. Which AI providers are contractually allowed (data residency concerns)?
5. Should admin alert notifications also go to a private Telegram admin group?
6. Is Hikvision in scope for MVP or later?
7. What is the official company legal name / tenant branding for the dashboard?
8. Existing ticketing tool to migrate from (email, Excel, another bot)?

---

## 8. Interim (Phases 1–5) support without deep software APIs

Until Phase 6 completes, the platform still delivers value via:

- Conversational diagnosis (UZ/RU)
- Screenshot analysis
- Voice transcription
- Verified KB / RAG
- Ticket routing to humans
- Agent-based OS/printer/network diagnostics (Phase 5)
- Human takeover from web dashboard

This is intentional: **do not block MVP on undocumented pharmacy APIs.**
