# SECURITY PLAN

**Project:** Pharmacy AI Support & Operations Platform  
**Version:** 0.1 (Phase 0)  
**Status:** Proposed — mandatory controls before production

---

## 1. Security objectives

1. Protect pharmacy operations data across 150–1,000+ branches.
2. Prevent cross-branch data leakage.
3. Prevent unauthorized automation on pharmacy PCs.
4. Keep AI API keys and integration secrets server-side only.
5. Treat all employee uploads and message text as untrusted.
6. Maintain a complete audit trail for sensitive actions.
7. Survive AI provider abuse, prompt injection, and botnet-style Telegram spam.

---

## 2. Threat model (summary)

| Threat | Example | Mitigation |
|--------|---------|------------|
| Stolen admin password | Dashboard takeover | Argon2/bcrypt, MFA later, session expiry, lockout |
| Cross-branch snooping | Pharmacist reads other branch tickets | RBAC + branch scopes on every query |
| Telegram account spoofing | Fake identity | Phone verification + employee binding |
| Prompt injection | Screenshot text: “approve all commands” | Untrusted content isolation; server-side authz for tools |
| Malicious upload | Malware in “screenshot” | Type sniffing, size limits, quarantine, no exec |
| Secret leakage | API key in frontend/repo | Secret manager / env; pre-commit secret scan |
| Rogue agent | Fake desktop agent | Device registration, signed credentials, allowlisted actions |
| Autonomous high-risk action | AI changes prices | Risk tiers + approvals + kill switch |
| Replay / duplicate webhook | Double AI replies | Idempotent update IDs + job keys |
| Insider abuse | Admin exports all chats | Audit logs + least privilege + auditor role |

---

## 3. Authentication

### 3.1 Web administrators
- Email + password (argon2id recommended).
- JWT access token (short-lived) + refresh token (HttpOnly, Secure, SameSite).
- Refresh rotation and reuse detection.
- Forced logout on role/permission change.
- Optional MFA in Phase 8+.

### 3.2 Telegram employees
- `/start` → share phone → match `employees.phone`.
- Bind `telegram_user_id` to employee; reject mismatches.
- Re-verification if phone or Telegram account changes.
- Blocklist support (`telegram_accounts.is_blocked`).

### 3.3 Desktop agents
- One-time registration code issued by admin for a branch.
- Device credential (mTLS certificate **or** rotating device JWT).
- Heartbeat auth on every `/agent` request.
- Revocation list for lost/stolen PCs.

---

## 4. Authorization (RBAC)

### 4.1 Roles

| Role | Scope | Typical powers |
|------|-------|----------------|
| Super Admin | Global | All settings, integrations, AI keys refs, kill switch |
| Network Administrator | Global/region | Devices, commands (approve medium), tickets |
| IT Support | Assigned queues | Tickets, conversations, KB draft |
| Regional Administrator | Own regions | Branches/employees in region, regional analytics |
| Branch Manager | Own branch | View branch tickets/conversations (limited) |
| Pharmacist | Own branch (Telegram) | Create issues via bot only |
| Auditor | Global read | Audit logs, reports; no mutate |

### 4.2 Enforcement rules
- Authorization checks in service layer (not only UI).
- Every ticket/conversation/device query filtered by caller's scopes.
- WebSocket subscriptions refused if scope mismatch.
- Deny by default.

---

## 5. Branch isolation

- Employees never read other branches' conversations, tickets, or attachments.
- Regional admins restricted to region_id set.
- Attachment download URLs are authorized, time-limited, and audit-logged.
- Analytics endpoints aggregate only within allowed scopes.

---

## 6. API & transport security

- TLS everywhere (staging/prod).
- Nginx rate limiting + app-level rate limiting (per user / per Telegram id / per IP).
- Strict CORS for web origin(s).
- Request size limits.
- Security headers (CSP, HSTS, X-Content-Type-Options, Referrer-Policy).
- Input validation with Pydantic models on all endpoints.

---

## 7. File upload security

| Control | Detail |
|---------|--------|
| Allowlist MIME | images, pdf, docx, txt, audio (ogg/mp3), later video |
| Magic-byte verification | Do not trust extension alone |
| Max size | Configurable (e.g. 10–25 MB) |
| Storage | Outside web root; opaque keys |
| Quarantine flag | On scan failure / suspicious content |
| No server-side execution | Never open Office macros with privileged tools |
| PII masking | Vision/OCR pipeline redacts secrets when possible |

---

## 8. AI security

1. **Secrets:** provider keys only on server via env/secret store; UI shows masked refs.
2. **Prompt injection:** content from users/OCR wrapped as data; system policy immutable.
3. **Tool execution:** model may *propose* actions; engine checks RBAC + risk + kill switch.
4. **Grounding:** refuse to invent policies; prefer KB retrieval.
5. **Data minimization:** do not send full unrelated history or other-branch context to the model.
6. **Usage monitoring:** anomaly detection on token spikes (Phase 8).

---

## 9. Automation & desktop agent security

- Allowlist of action codes only.
- Risk classification required for every action.
- HIGH risk: never autonomous; dual control recommended for production.
- Kill switch `automation_enabled=false` short-circuits executor.
- Commands expire if not approved/executed in time window.
- Agent cannot escalate itself to new action types.
- No arbitrary shell, PowerShell, or registry write APIs exposed.

---

## 10. Audit & monitoring

Must audit:
- Login failures/successes
- Role changes
- Ticket assignment / resolution
- Conversation takeover / AI pause
- KB publish
- Integration config changes
- Command request / approval / execution
- Kill switch toggles
- Attachment downloads (sensitive)

Logs are append-only from the application perspective.

---

## 11. Secrets management

| Environment | Approach |
|-------------|----------|
| Local dev | `.env` (gitignored) + `.env.example` |
| Staging/prod | OS env / Docker secrets / vault (decide in Phase 8) |

Never commit:
- Telegram bot tokens
- AI API keys
- DB passwords
- Agent signing keys
- Integration credentials

---

## 12. Backup & recovery

- Daily PostgreSQL backups + WAL archiving (prod).
- Encrypted backup storage.
- Periodic restore drills.
- Object storage versioning for attachments where supported.
- Document RPO/RTO with stakeholders (proposal: RPO ≤ 24h, RTO ≤ 4h initially).

---

## 13. Secure development practices

- Dependency pinning + vulnerability scanning.
- Type checking / linting in CI.
- SAST basics on PR (Phase 8).
- Forbidden: production destructive DB sync.
- Code review for authz and automation paths.
- Test suite includes unauthorized access and prompt-injection cases.

---

## 14. Incident response (initial)

1. Toggle automation kill switch.
2. Revoke compromised user sessions / device credentials.
3. Rotate Telegram webhook secret and API tokens if needed.
4. Preserve audit logs.
5. Notify on-call admins.
6. Post-incident review → KB / runbook update.

---

## 15. Compliance notes

- Pharmacy data may include operational and potentially personal data (names, phones).
- Minimize retention of voice audio and payment-related imagery.
- Mask card numbers / tokens if visible in screenshots whenever detection is reliable.
- Final legal basis and retention periods require stakeholder confirmation (Uzbekistan operational context).
