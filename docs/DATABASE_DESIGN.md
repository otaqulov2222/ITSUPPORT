# DATABASE DESIGN

**Project:** Pharmacy AI Support & Operations Platform  
**Version:** 0.1 (Phase 0)  
**Engine:** PostgreSQL 16 + pgvector  
**Migrations:** Alembic only (no destructive prod sync)

---

## 1. Design principles

- Normalized core entities with explicit FKs.
- Soft delete (`deleted_at`) for users, employees, branches, articles where recovery matters.
- Branch-scoped authorization enforced in application **and** query filters.
- UUID primary keys for externally visible IDs; optional bigserial internals where useful.
- Every sensitive mutation leaves an `audit_logs` row.
- Embeddings stored via pgvector on `document_chunks`.
- Never use production `DROP` / wipe sync; expand-contract migrations only.

---

## 2. Organizational hierarchy

```
companies
  └── regions
        └── branches
              ├── employees
              ├── devices
              └── (tickets, conversations scoped by branch)
```

Initial deployment may use a single `companies` row; schema remains multi-branch ready from day one.

---

## 3. Core tables (logical schema)

### 3.1 Identity & access

#### `users`
Web login accounts (admins, auditors, support).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | CITEXT UNIQUE | |
| password_hash | TEXT | argon2/bcrypt |
| full_name | TEXT | |
| phone | TEXT NULL | |
| is_active | BOOLEAN | |
| last_login_at | TIMESTAMPTZ | |
| created_at / updated_at / deleted_at | TIMESTAMPTZ | soft delete |

#### `roles`
| Column | Type |
|--------|------|
| id | UUID PK |
| code | TEXT UNIQUE | `SUPER_ADMIN`, `NETWORK_ADMIN`, `IT_SUPPORT`, `REGIONAL_ADMIN`, `BRANCH_MANAGER`, `PHARMACIST`, `AUDITOR` |
| name | TEXT |
| description | TEXT |

#### `permissions`
| Column | Type |
|--------|------|
| id | UUID PK |
| code | TEXT UNIQUE | e.g. `tickets.assign`, `automation.approve` |
| description | TEXT |

#### `role_permissions`
| role_id | permission_id | PK composite |

#### `user_roles`
| user_id | role_id | scope_type (`GLOBAL`/`REGION`/`BRANCH`) | scope_id NULL |

#### `employees`
Pharmacy staff (Telegram-facing). May or may not have a `users` account.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| branch_id | UUID FK → branches | required |
| user_id | UUID FK → users NULL | if also web user |
| employee_code | TEXT | unique per company |
| full_name | TEXT | |
| phone | TEXT | unique-ish; verification target |
| position | TEXT | |
| role_code | TEXT | pharmacist / manager ... |
| is_active | BOOLEAN | |
| created_at / updated_at / deleted_at | | |

#### `telegram_accounts`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| employee_id | UUID FK NULL | set after verification |
| telegram_user_id | BIGINT UNIQUE | |
| telegram_chat_id | BIGINT | |
| username | TEXT NULL | |
| phone | TEXT NULL | |
| phone_verified_at | TIMESTAMPTZ NULL | |
| language_code | TEXT | `uz`/`ru`/`en` |
| is_blocked | BOOLEAN | |
| created_at / updated_at | | |

---

### 3.2 Organization

#### `companies`
| id | name | settings JSONB |

#### `regions`
| id | company_id | name | code | is_active |

#### `branches`
| id | region_id | code | name | address | phone | timezone | is_active | metadata JSONB |

Indexes: `(region_id)`, `(code)` unique per company via join or denormalized `company_id`.

---

### 3.3 Conversations & messages (unified bus)

#### `conversations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| branch_id | UUID FK | |
| employee_id | UUID FK | |
| telegram_account_id | UUID FK | |
| channel | TEXT | `TELEGRAM` |
| status | TEXT | `OPEN`, `WAITING`, `RESOLVED`, `CLOSED` |
| ai_enabled | BOOLEAN DEFAULT TRUE | pause/resume |
| taken_over_by | UUID FK users NULL | |
| subject | TEXT NULL | |
| last_message_at | TIMESTAMPTZ | |
| created_at / updated_at | | |

#### `messages`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| conversation_id | UUID FK | |
| sender_type | TEXT | `EMPLOYEE`, `AI`, `ADMIN`, `SYSTEM` |
| sender_user_id | UUID NULL | admin |
| sender_employee_id | UUID NULL | |
| content_text | TEXT NULL | |
| content_type | TEXT | `TEXT`, `IMAGE`, `VOICE`, `DOCUMENT`, `SYSTEM` |
| language | TEXT NULL | |
| telegram_message_id | BIGINT NULL | |
| ai_model | TEXT NULL | |
| ai_confidence | TEXT NULL | `VERIFIED`/`LIKELY`/`UNVERIFIED` |
| metadata JSONB | | OCR snippets, intents |
| created_at | TIMESTAMPTZ | |
| idempotency_key | TEXT NULL UNIQUE | |

#### `attachments`
| id | message_id | storage_key | mime_type | size_bytes | checksum | kind (`IMAGE`/`VOICE`/`DOCUMENT`/`VIDEO`) | is_quarantined | created_at |

#### `conversation_events`
For realtime/audit of takeover, AI pause, etc.

| id | conversation_id | event_type | actor_user_id | payload JSONB | created_at |

---

### 3.4 Tickets

#### `tickets`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| number | BIGSERIAL / human code | e.g. `T-2026-000123` |
| branch_id | UUID FK | |
| employee_id | UUID FK | |
| conversation_id | UUID FK NULL | |
| category | TEXT | POS, PRINTING, NETWORK, SOFTWARE, INVENTORY, SALES, PAYMENT, ACCESS, HARDWARE, OTHER |
| priority | TEXT | CRITICAL/HIGH/MEDIUM/LOW |
| status | TEXT | see lifecycle |
| title | TEXT | |
| description | TEXT | |
| ai_diagnosis | TEXT NULL | |
| assigned_to | UUID FK users NULL | |
| sla_due_at | TIMESTAMPTZ NULL | |
| resolved_at / closed_at | TIMESTAMPTZ | |
| resolution_summary | TEXT NULL | |
| created_at / updated_at | | |

**Lifecycle:**  
`NEW → AI_DIAGNOSING → WAITING_FOR_EMPLOYEE → AI_RESOLVING → HUMAN_SUPPORT → IN_PROGRESS → RESOLVED → CLOSED`  
(+ `REOPENED` transition back to `HUMAN_SUPPORT` / `IN_PROGRESS`)

#### `ticket_assignments`
| id | ticket_id | assignee_id | assigned_by | assigned_at | unassigned_at |

#### `ticket_events`
| id | ticket_id | actor_type | actor_id | event_type | from_status | to_status | comment | visibility (`INTERNAL`/`EMPLOYEE`) | created_at |

#### `ticket_links`
Optional duplicate detection: `ticket_id`, `related_ticket_id`, `relation` (`DUPLICATE`/`RELATED`)

---

### 3.5 Knowledge base & RAG

#### `knowledge_articles`
| Column | Type |
|--------|------|
| id | UUID PK |
| title | TEXT |
| category | TEXT |
| description | TEXT |
| problem | TEXT |
| symptoms | TEXT |
| root_cause | TEXT |
| solution | TEXT |
| steps JSONB | ordered steps |
| related_software TEXT[] | |
| applicable_branch_ids UUID[] NULL | null = all |
| applicable_device_types TEXT[] | |
| author_id | UUID |
| version | INT |
| status | `DRAFT`/`APPROVED`/`DEPRECATED` |
| last_reviewed_at | TIMESTAMPTZ |
| created_at / updated_at / deleted_at |

#### `knowledge_documents`
Uploaded source files (PDF/DOCX/TXT/images/video metadata).

| id | title | source_type | storage_key | mime_type | uploaded_by | processing_status | created_at |

#### `document_chunks`
| id | document_id | article_id NULL | chunk_index | content | embedding vector(dim) | metadata JSONB | token_count |

Indexes: HNSW/IVFFlat on `embedding`; GIN on metadata as needed.

---

### 3.6 AI configuration & usage

#### `ai_provider_configs`
| id | provider | capability | model_name | is_default | is_fallback | config JSONB (non-secret) | secret_ref | is_active |

Secrets stored via env/secret manager; `secret_ref` is a pointer, not the key.

#### `ai_usage_logs`
| id | provider | model | capability | conversation_id NULL | ticket_id NULL | input_tokens | output_tokens | cost_estimate | latency_ms | status | error | created_at |

---

### 3.7 Devices & automation

#### `devices`
| id | branch_id | hostname | agent_version | os_info JSONB | device_fingerprint | status | last_seen_at | registered_at |

#### `device_credentials`
| device_id | public_key / hashed_token | rotated_at | revoked_at |

#### `device_commands`
| id | device_id | action_code | risk_level | requested_by | branch_id | payload JSONB | status | created_at |

#### `command_approvals`
| id | command_id | approver_id | decision | reason | decided_at |

#### `command_executions`
| id | command_id | started_at | finished_at | result_status | result_payload JSONB | error |

#### `system_settings`
| key | value JSONB | updated_by | updated_at |  
Includes `automation_enabled` kill switch.

---

### 3.8 Integrations

#### `integration_configs`
| id | system_code (`F_APTEKA`, `FOM`, ...) | branch_id NULL | config JSONB | secret_ref | health_status | last_health_at | is_active |

#### `integration_health_logs`
| id | integration_id | status | details JSONB | checked_at |

---

### 3.9 Notifications & audit

#### `system_notifications`
| id | audience_type | audience_id | severity | title | body | link_type | link_id | read_at | created_at |

#### `audit_logs`
| id | actor_user_id NULL | actor_type | action | resource_type | resource_id | branch_id NULL | ip | user_agent | before JSONB | after JSONB | created_at |

Immutable insert-only table; no updates/deletes from app.

---

## 4. Essential indexes

- `employees(branch_id)`, unique `(branch_id, phone)` where active
- `telegram_accounts(telegram_user_id)` unique
- `conversations(branch_id, last_message_at DESC)`
- `messages(conversation_id, created_at)`
- `tickets(status, priority, sla_due_at)`
- `tickets(branch_id, created_at DESC)`
- `audit_logs(created_at DESC)`, `(resource_type, resource_id)`
- `ai_usage_logs(created_at)`, `(provider, created_at)`
- `document_chunks` vector index
- `devices(branch_id, last_seen_at)`

---

## 5. Analytics (no fake stats)

Dashboard metrics are SQL aggregations over live tables, e.g.:

- Total / active branches → `branches`
- Registered / online employees → `employees` + recent `telegram` / agent heartbeats
- Open / resolved tickets → `tickets`
- Average resolution time → `resolved_at - created_at`
- AI resolution rate → tickets resolved without `HUMAN_SUPPORT` (definition documented in code)
- Top problems → `tickets.category` / classified intents
- Recurring branches → ticket counts with thresholds

Materialized views may be added in Phase 4/8 for heavy reports; never hardcode demo numbers in UI.

---

## 6. Migration strategy

1. Alembic revisions only.
2. Expand → migrate → contract for breaking changes.
3. Seed roles/permissions in a controlled data migration.
4. Staging restore-test before production migrate.
5. Forbidden in production: `Base.metadata.drop_all`, prune-without-backup, force push schema.

---

## 7. Data retention (initial policy proposal)

| Data | Proposal |
|------|----------|
| Conversation messages | 24 months online; archive thereafter |
| Attachments | 12–24 months; quarantine malware indefinitely until purge |
| Audit logs | 36 months minimum |
| AI usage logs | 12 months |
| Voice raw audio | Optional shorter retention after STT (configurable) |

Finalize with legal/compliance stakeholders before production.
