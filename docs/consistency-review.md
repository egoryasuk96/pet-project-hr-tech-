# Consistency Review — Documentation Cleanup

**Продукт:** Employee Service  
**ID:** DOC-CONSISTENCY  
**Версия:** 1.0  
**Статус:** Pre-merge cleanup (`docs-restructure` → `main`)  
**Дата:** 2026-09-20  

**Назначение:** единый реестр editorial safe-fixes и открытых противоречий по всей документации.  
**Правило:** пункты со статусом `OPEN` **не** закрываются в этом проходе; бизнес-решения не принимаются.

Связанные артефакты:

- Канон live config: [ADR-LIVE-CFG-01](./03-diagrams/architecture/adr-live-config.md), [erd-domain-model.md](./03-diagrams/erd/erd-domain-model.md)
- Deprecated snapshot: [Snapshot Model](./03-diagrams/erd/snapshot-model.md), [ADR-SNAP-01](./03-diagrams/architecture/adr-snapshot-submit-versions.md) (Superseded)
- API-специфичные open questions (не редактировались в этом проходе): [api-contract-analysis.md §10](./04-api/api-contract-analysis.md)

---

## 1. SAFE-FIXED

| ID | Что исправлено | Источник канона | Файлы |
| :--- | :--- | :--- | :--- |
| SF-01 | Устаревшие «route snapshot» / «Route snapshot» → **RouteInstance** | Snapshot Model §2, glossary | UML, BPMN, Architecture, AC, BR, FR (где о маршруте) |
| SF-02 | «schema/value snapshot» + «Обновляется» → **FieldValueVersion** append-only | Snapshot Model §2, ADR-SNAP-01 | `uml-description.md`, `use-case-overview.md`, BPMN-03, component-diagram |
| SF-03 | BR-17 **Связи:** `AC-APP-05` → `AC-APP-05b`; текст «snapshot маршрута» → RouteInstance | AC-APP-05b, таблица трассировки BR | `business-rules.md` |
| SF-04 | BR-20: задачи **первого** этапа (не двусмысленное «текущего») | BR-06, Snapshot Model §4, OQ-B | `business-rules.md`, `data-flows.md` |
| SF-05 | FR-APP-03: убран ошибочный `BR-17` из Связей и сводной таблицы | FR-APP-07 владеет BR-17 | `functional-requirements.md` |
| SF-06 | FR-APP-06/07: «snapshot» (маршрут) → **RouteInstance** | Snapshot Model | `functional-requirements.md` |
| SF-07 | AC-APP-02 / §10 AC-APP-10/10b: snapshot маршрута → RouteInstance | Snapshot Model | `acceptance-criteria.md` |
| SF-08 | NFR-SEC-02 трассировка: убран `AC-ACC-01` (это 404 / NFR-SEC-05) | NFR-SEC-05, ACL-01 | `non-functional-requirements.md` |
| SF-09 | Stub xref: ACL-04 / ACL-09 не определены в Baseline rbac-matrix | backlog AC-ACC-04 | `rbac-matrix.md`, Future-диаграммы (пометка) |
| SF-10 | Glossary: EN-якоря терминов; шапка версии 1.1 | план cleanup | `glossary.md` |
| SF-11 | Hub README: Stage 4.1 analysis + ссылка на этот реестр | план cleanup | `README.md` |
| SF-12 | DD FK-имена: `route_snapshot_id` → `route_instance_id`; `snapshot_stage_id` → `instance_stage_id` | ERD domain model | `data-dictionary.md` |
| SF-13 | DD `assignment_kind`: `both` → `role_and_user` | ERD enum table | `data-dictionary.md` |
| SF-14 | DD ApprovalTask: добавлен `decided_at` (уже в ERD Mermaid) | `erd-domain-model.md` | `data-dictionary.md` |
| SF-15 | UML-CL-01 + ARCH-CMP §6: **RequestFieldValue** (working values) — sync с ERD/Snapshot | Snapshot §3, DD §4.2, ERD | `class-domain-model.md`, `component-diagram.md` |
| SF-16 | Backlog: пустые orphan-секции свёрнуты; AC-ACC-04 ACL-пометка | план cleanup | `backlog.md` |
| SF-17 | UML-CL-01: устаревшая рамка «ERD позже» → ERD уже Baseline | `erd/` | `class-domain-model.md` |
| SF-18 | E0–E1 docs: snapshot → live config; RouteInstance/FieldValueVersion deprecated | ADR-LIVE-CFG-01, erd-domain-model v2 | glossary, ERD-DD, UML, BPMN, Architecture, FR/AC/UC/NFR, API analysis, openapi descriptions, README |
| SF-20 | Docs-pass: ADR-ERR-03 envelope; ADR-ID-01 Target OpenAPI; BR-16 one role; Target API без snapshot fields | ADR-ERR-03, ADR-ID-01, ADR-ORG-01, ADR-LIVE-CFG-01 | error-matrix, api-contract-analysis, approval-api-contract, openapi.yaml, Vision, RBAC, context |
| SF-21 | Architecture Frozen Target sync: JWT CURRENT; demo-header Superseded; Action Engine primary mutation; Notification Target | ADR-AUTH-JWT-01, ADR-ACTION-01, ADR-LIVE-CFG-01 | ARCH-*, Vision §7.1/§10, README, backlog auth/notif status |

**Примечание SF-18 (HISTORICAL):** на момент E0–E1 docs описывали target при возможном lag кода до E2. После E2+ / Frozen Target runtime docs и target совпадают; snapshot-сущности в CURRENT не утверждаются.

**Примечание SF-01…07:** rename к RouteInstance/FieldValueVersion — **historical audit trail** (pre-live-config); не CURRENT wording.

---

## 2. OPEN — REQUIRES REVIEW

Бизнес / контракт / модель **не** решены. При необходимости в документах — только короткая ссылка сюда.

### 2.1. Явно оставлены OPEN (обязательный список)

| ID | Тема | Источники | Противоречие | Статус |
| :--- | :--- | :--- | :--- | :--- |
| RR-AUTHZ-01 | 403 vs 404 / task & request visibility | NFR-SEC-02 («→ 403») vs NFR-SEC-05 / ACL-01 / AC-ACC-01 (404); FR-REQ-04/06; FR-APP-02; api-analysis §10.6 | Когда `ERR_FORBIDDEN`/`403`, когда `ERR_NOT_FOUND`/`404` | OPEN |
| RR-TASK-01 | Статус ApprovalTask при reject/return | FR-APP-04/05, BR-04/05, AC-APP-06/07 («закрыты») vs enum `completed`\|`cancelled`; api-analysis §3.15–3.16 | Какой terminal status у actor-задачи и siblings | OPEN |
| RR-TYPE-01 | Inactive type + submit/resubmit | BR-10 («живые заявки продолжают обрабатываться») vs FR-REQ-03 / Error Matrix (`ERR_INACTIVE_TYPE` на submit) | Разрешён ли resubmit из `returned`, если тип уже `is_active=false` | OPEN |
| RR-COMMENT-01 | Free comment — полный набор статусов | FR-REQ-06 («включая `in_approval`») vs BR-28 / AC-REQ-06 / RBAC (явно `in_approval`); api §10.8 | Разрешены ли free comments вне `in_approval` | OPEN |
| RR-CAT-01 | FR-CAT-02 dual error | FR-CAT-02: `ERR_NOT_FOUND` / `ERR_INACTIVE_TYPE`; Error Matrix ограничивает `ERR_INACTIVE_TYPE` create/submit; api §10.2 | Какой код для GET неактивного типа | OPEN |
| RR-TASK-02 | ApprovalTask `created_at` / дата очереди | FR-APP-01 требует дату в очереди; DD/ERD ApprovalTask без `created_at`; api §10.4 | Добавить поле в модель или убрать из контракта | OPEN |
| RR-HIST-01 | HistoryEvent ↔ FieldValueVersion | Target: FieldValueVersion удалён; HistoryEvent без FK на версии | — | **Closed (target)** |
| RR-FK-01 | value_version_id на ApprovalTask | Target: поле удалено ([ADR-LIVE-CFG-01](./03-diagrams/architecture/adr-live-config.md)) | — | **Closed (target)** |

### 2.2. Прочие OPEN (полный inventory)

| ID | Тема | Источники | Противоречие | Статус |
| :--- | :--- | :--- | :--- | :--- |
| RR-ACL-01 | Семантика ACL-04 / ACL-09 | backlog AC-ACC-04; BPMN-03; sequence-admin; architecture-traceability | ID ссылаются, определений в Baseline rbac-matrix нет (stub xref = SF-09; семантика — open) | OPEN |
| RR-ROUTE-01 | BR-18 dual error на активации типа | BR-18: `ERR_ROUTE_CONFIG` или `ERR_VALIDATION`; submit уже `ERR_ROUTE_CONFIG` | Единый код для activate | OPEN |
| RR-API-01 | Demo headers | api-analysis §10.1 | HISTORICAL: demo-header Superseded; AuthN = JWT ([ADR-AUTH-JWT-01](./03-diagrams/architecture/adr-jwt-core-api.md)) | **Closed (target)** |
| RR-API-02 | Dictionary items в schema response | api-analysis §10.3 | Встроить items или отдельный endpoint | OPEN |
| RR-API-03 | Approver card route | api-analysis §10.5 | Только `GET /approval-tasks/{id}` vs ещё `GET /requests/{id}` | OPEN |
| RR-API-04 | Cancelled-from-returned card values | api-analysis §10.7 | Target: working RequestFieldValue; FieldValueVersion удалён | **Closed (target)** |
| RR-API-05 | History pagination | api-analysis §10.9 | Нужна ли пагинация истории | OPEN |
| RR-API-06 | Pagination envelope | api-analysis §10.10 | page/cursor + response shape | OPEN |
| RR-API-07 | Error JSON envelope | api-analysis §10.11 | Рекомендация Error Matrix vs обязательный контракт | OPEN |
| RR-API-08 | OpenAPI `x-requirement` US vs UC/FR | api-analysis §10.12; `.cursor/rules/20-api.mdc` | Формат трассировки в OpenAPI | OPEN |

API-пункты RR-API-* дублируют [api-contract-analysis.md §10](./04-api/api-contract-analysis.md) для единого реестра; сам файл Stage 4.1 **не** изменялся в этом проходе.

---

## 3. Вне scope этого cleanup

- Изменения `docs/04-api/api-contract-analysis.md` (зафиксирован commit `dada33b`)
- Изменения `docs/04-api/openapi.yaml` (Stage 4.2)
- Закрытие любого `OPEN` пункта
- Переименование / перенумерация FR / UC / AC / BR / ACL ID
- Изменения кода приложения

---

## 4. История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Первый consistency pass перед merge `docs-restructure` |
