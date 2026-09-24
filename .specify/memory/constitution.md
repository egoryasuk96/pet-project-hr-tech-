<!--
Sync Impact Report
- Version change: 1.0.1 → 1.1.0
- Modified principles: Spec Kit & Change Discipline (Source of Truth
  hierarchy + conflict rule; closes Finding F-02)
- Added sections: none (material expansion of existing Change Discipline)
- Removed sections: none
- Follow-up TODOs: none
- Notes: F-01 closed — frontend is static HTML/JS, not Web SPA / React / Vue.
  F-02 closed — layered SoT; no automatic priority of code over approved
  Target docs (or vice versa) on conflict.
-->

# Employee Service Constitution

## Core Principles

### I. Documentation-First Portfolio

Employee Service is a **system-analyst portfolio** project. Analytical
documentation under `docs/` is the primary deliverable; application code
supports and demonstrates documented scenarios.

MUST NOT invent business features, endpoints, or schema elements solely
because they are common in HR/approval products. Scope is limited to
documented MVP / Target-active requirements (see `docs/`, `docs/backlog.md`).

Significant architectural deviations MUST be recorded as ADR under
`docs/03-diagrams/architecture/`.

### II. Fixed Technology Stack

Non-negotiable runtime stack:

- **Backend:** FastAPI (Python), single deployable API process.
- **Database:** PostgreSQL; schema changes via Alembic migrations.
- **Frontend:** static HTML/JavaScript web client, served by FastAPI
  ([ADR-UI-01](../../docs/03-diagrams/architecture/adr-static-web-client.md)).
  MUST NOT be called a «Web SPA». MUST NOT introduce React, Vue, or another
  frontend framework.

Secrets (DB URL, JWT secret, demo passwords) MUST live only in environment
variables — never in repository files.

Auth Target: JWT access token (`POST /auth/login`, Bearer). Refresh tokens
MUST NOT be added without a dedicated architectural decision
([ADR-AUTH-JWT-01](../../docs/03-diagrams/architecture/adr-jwt-core-api.md)).

### III. Modular Monolith Boundaries

Architecture MUST remain a **modular monolith**: one backend, one database,
logical modules inside the process — not independently deployable services.

MUST NOT introduce:

- microservices / service mesh splits;
- event sourcing;
- message brokers (Kafka, RabbitMQ, etc.) without a separate ADR;
- a separate workflow / BPM engine product;
- snapshot / process-versioning of workflow configuration in the Target model
  without a separate ADR.

References: [architecture-description.md](../../docs/03-diagrams/architecture/architecture-description.md),
[ADR-LIVE-CFG-01](../../docs/03-diagrams/architecture/adr-live-config.md).

### IV. Live Configurable Workflow

Workflow configuration is a **live / configurable** model read at runtime:

`Process → RequestType → ApprovalRoute → ApprovalStage → StageAssignment`,
plus **`ProcessTransition`** (and related Status / Action catalogs).

Target MUST NOT reintroduce snapshot entities or fields such as
`RouteInstance*`, `FieldValueVersion`, `value_version_id`, or equivalents
([ADR-LIVE-CFG-01](../../docs/03-diagrams/architecture/adr-live-config.md),
[ADR-ACTION-01](../../docs/03-diagrams/architecture/adr-configurable-actions.md)).

Primary mutation path for status / approval effects is the Action Engine
over live `ProcessTransition` rows — not hardcoded Python matrices as the
source of allowed actions.

### V. Identity, Roles, and Identifiers

Roles in Target: **`employee`**, **`approver`**, **`admin`**.

- Each `User` has exactly one `role_id`. M:N `UserRole` MUST NOT be used
  ([ADR-ORG-01](../../docs/03-diagrams/architecture/adr-org-model.md), BR-16).
- `User` primary key is **UUID**.
- Other business entities use **integer** IDs unless a confirmed need and ADR
  justify another type ([ADR-ID-01](../../docs/03-diagrams/architecture/adr-id-strategy.md)).

`Request` Target shape (core identity / workflow pointers):

- `id`, `request_type_id`, `initiator_user_id`, `status_id`, `current_stage_id`
- `current_stage_id` MAY be `NULL` after workflow completion (e.g. approved /
  rejected / cancelled terminal paths).

### VI. Approval Business Invariants

- **Self-approval is forbidden** (initiator MUST NOT approve / reject / return
  their own request) — BR-21.
- **Reject** and **return** on an approval stage REQUIRE a non-empty comment —
  BR-25. Approve comment is optional.

Detailed route / first-approve / visibility rules remain in
`docs/02-requirements/business-rules.md` and RBAC matrix; this constitution
does not duplicate them.

### VII. Transactional History and Notifications

On a **successful** workflow action, `HistoryEvent` (and in-app
`Notification` when that module is in scope) MUST be created in the **same
database transaction** as the business mutation. Failure to persist side
effects MUST roll back the business change (BR-24, BR-29; ADR-TX-* in
data-flows).

### VIII. Target API Contract

- Primary workflow execute: `POST /requests/{request_id}/actions/{action_id}`.
- `available_actions` (discovery) is part of the Target API
  (`GET /requests/{request_id}/available-actions`).
- Legacy submit / approve / reject / return / cancel style endpoints MUST NOT
  become the primary API again. Thin deprecated aliases may exist; new clients
  and features MUST use Action Engine paths
  ([ADR-ACTION-01](../../docs/03-diagrams/architecture/adr-configurable-actions.md)).
- Target error envelope:
  `{ "error": { "code", "message", "details" } }`
  ([ADR-ERR-03](../../docs/03-diagrams/architecture/adr-error-envelope.md)).

Contract details: `docs/04-api/openapi.yaml` (Frozen Target).

## Domain & Data Invariants

This section restates non-negotiable domain constraints for Spec Kit plans
and implementations. It is not a substitute for ERD or OpenAPI.

| Invariant | Rule |
| :--- | :--- |
| Live config | Runtime reads route / transitions; no Target snapshots |
| Request keys | `id`, `request_type_id`, `initiator_user_id`, `status_id`, `current_stage_id` |
| Stage pointer | `current_stage_id` nullable when workflow finished |
| IDs | User UUID; other business PKs integer by default |
| Roles | Single `role_id`; no `UserRole` |
| Self-approval | Forbidden |
| Decision comments | Required for reject / return |
| Side effects | History (+ notifications) same TX as success path |

Canonical models: `docs/03-diagrams/erd/`, domain packages under `app/domain/`.

## Spec Kit & Change Discipline

1. Spec Kit features MUST align with this constitution and existing `docs/`.
2. Do not regenerate the product from scratch; extend only what Target docs
   and Frozen API already define.
3. Source of Truth hierarchy (Finding F-02 closed):
   a. **Approved requirements / Frozen Target** define WHAT the system
      MUST do (Target-active scope in `docs/`, including Frozen Target
      markers in `docs/backlog.md`).
   b. **ADR** define approved architectural decisions and constraints.
   c. **Frozen OpenAPI** (`docs/04-api/openapi.yaml`) is the public API
      contract.
   d. **Code + runtime** are the factual source for HOW the system
      currently behaves.
   e. **BPMN / UML / C4 / ERD / glossary** document the agreed model and
      MUST stay aligned with (a)–(d).
   f. **Backlog / Future / Legacy** markings MUST NOT be treated as
      Target-active without an explicit promotion decision.

   Conflict rule: if (a)/(b)/(c) disagree with (d), **no source
   automatically wins**. Record the discrepancy and decide whether
   runtime is a defect or documentation is stale; fix via a separate
   deliberate change. If runtime already implements Target-active
   behavior but BPMN/UML/glossary/other docs do not reflect it, that is
   **documentation drift** to be synchronized — not a silent third
   interpretation, and not an automatic “code overrides docs” rule.
4. Ambiguous or undocumented requirements MUST be surfaced (clarify / ADR),
   not assumed from industry defaults.
5. Constitution changes follow Governance below; application/runtime changes
   are out of scope of `/speckit-constitution`.

## Governance

- This constitution governs Spec Kit workflows (specify → plan → tasks →
  implement) and agent guidance for Employee Service.
- Amendments require: updated `constitution.md`, semantic version bump,
  Sync Impact Report (temporary HTML comment), and alignment check against
  `docs/` ADR index.
- Versioning: **MAJOR** — remove/redefine a non-negotiable principle;
  **MINOR** — add or materially expand a principle/section;
  **PATCH** — clarification / wording only.
- Compliance: PRs and Spec Kit plans MUST NOT violate Core Principles or
  Domain & Data Invariants without an Accepted ADR that amends Target.
- Related guidance: project Cursor rules (`.cursor/rules/`), Vision & Scope,
  Architecture index, OpenAPI Frozen Target.

**Version**: 1.1.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
