# ERD-MAP — Traceability

**Продукт:** Employee Service  
**ID:** ERD-MAP  
**Версия:** 1.1  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [README.md](./README.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [erd-domain-model.md](./erd-domain-model.md)

---

## 1. Назначение

Показать, какие требования, процессы и архитектурные модули поддерживаются сущностями / связями логической модели данных. Новые FR/BR **не** вводятся.

---

## 2. Сущности → требования

| Entity | FR | BR | UC (основные) |
| :--- | :--- | :--- | :--- |
| User, Role | FR-AUTH-01…03, FR-CAB-01 — **Future / backlog** | BR-16; BR-27 — backlog | UC-01, UC-02 — backlog |
| Company, Department, Employee | — (org data) | BR-12 (no auto-routing) | — |
| Process, Status, Action, ProcessTransition | — (Action Engine) | BR-20, BR-07 | UC-05, UC-07…09 |
| RequestType, RequestFieldDefinition | FR-CAT-01…03; FR-ADMIN-01…02 — **Future / backlog** | BR-10, BR-18, BR-26 | UC-03, UC-04; UC-11 — backlog |
| Dictionary, DictionaryItem | FR-CAT-03; FR-ADMIN-06 — **Future / backlog** | — | UC-11 — backlog |
| ApprovalRoute, ApprovalStage, StageAssignment | FR-ADMIN-03…05 — **Future / backlog** | BR-02, BR-08, BR-12, BR-18 | UC-05, UC-12 — backlog |
| Request | FR-REQ-01…09; FR-CAB-02, FR-ADMIN-07 — **Future / backlog** | BR-01, BR-07, BR-19, BR-20; BR-27 — backlog | UC-04…06, UC-10; UC-15 — backlog |
| RequestFieldValue | FR-REQ-02, FR-REQ-09 | BR-26 | UC-04, UC-05 |
| ApprovalTask | FR-APP-01…07 | BR-03…06, BR-15, BR-17, BR-21 | UC-07…09 |
| Comment | FR-REQ-06, FR-APP-03…05 | BR-25, BR-28 | UC-05, UC-07…09 |
| HistoryEvent | FR-AUDIT-01…02; FR-ADMIN-08 — **Future / backlog** | BR-24; retention NFR-LOG-02, NFR-LOG-03 п.2 | UC-14 (employee/approver Baseline; admin — backlog) |
| Notification (**Future / backlog**) | FR-NOTIF-01…03, FR-CAB-03 | BR-11, BR-23, BR-29 | UC-13 |

**Удалено из модели:** RouteInstance*, FieldValueVersion — см. [ADR-LIVE-CFG-01](../architecture/adr-live-config.md).

---

## 3. Критичные BR → поддержка моделью

| BR | Как поддерживается |
| :--- | :--- |
| BR-01 | Request.initiator_user_id; видимость — слой AuthZ |
| BR-02 | ApprovalStage.sequence_no; Request.current_stage_id → live stage |
| BR-03 | ApprovalTask.status open→completed/cancelled на одном stage_id |
| BR-04 / BR-05 / BR-17 | Request.status_id + закрытие задач этапа |
| BR-06 / BR-22 | Resubmit: current_stage_id → первый live-этап; новые ApprovalTask |
| BR-07 | Status + constraint cancel only draft/returned |
| BR-08 | Submit читает live ApprovalRoute/Stage/Assignment; создаёт ApprovalTask |
| BR-09 | Live config **может** влиять на in-flight; admin-ограничения (не удалять stage с open tasks) |
| BR-10 | RequestType.active |
| BR-11 / BR-23 / BR-29 | Notification entity (**Future / backlog**) |
| BR-12 | StageAssignment role/user; нет org auto-routing |
| BR-13 (**backlog**) / BR-14 | данные + AuthZ; Approver через ApprovalTask |
| BR-15 | ApprovalTask.assignee_user_id |
| BR-16 | User.role_id (одна роль на User в target) |
| BR-18 | валидация route на activate/submit |
| BR-19 / BR-20 | status draft → in_approval via ProcessTransition |
| BR-21 | initiator ≠ assignee |
| BR-24 | HistoryEvent; без обязательного полного payload |
| BR-25 | Comment.kind=decision + text required for reject/return |
| BR-26 | RequestFieldValue (working values) по live schema при edit/submit/display |
| BR-27 | create Request только с employee |
| BR-28 | Comment.kind=free при in_approval |

---

## 4. NFR retention (не смешивать)

| Store | NFR | Retention | ERD |
| :--- | :--- | :--- | :--- |
| HistoryEvent (прикладной аудит) | NFR-LOG-02, NFR-LOG-03 п.2 | **60 дней** | Да |
| Technical API logs | NFR-LOG-01, NFR-LOG-03 п.1 | **14 дней** | **Нет** (infra) |

---

## 5. BPMN → сущности

| BPMN | Сущности |
| :--- | :--- |
| BPMN-01 Request lifecycle | Request, RequestFieldValue, ApprovalTask, HistoryEvent, Comment; live ApprovalRoute/Stage; Notification — **Future / backlog** |
| BPMN-02 Approval stage | ApprovalTask, Request (current_stage_id), live ApprovalStage, Comment, HistoryEvent; Notification — **Future / backlog** |
| BPMN-03 Admin configure | RequestType, FieldDefinition, ApprovalRoute/Stage/Assignment, ProcessTransition, Dictionary*; live config **может** затронуть in-flight ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)) |

---

## 6. UML → сущности

| UML | Сущности |
| :--- | :--- |
| UML-CL-01 | Все основные классы target ERD v2 |
| UML-SM-01 | Request.status_id, current_stage_id |
| UML-SEQ-01 | live route → ApprovalTask; HistoryEvent |
| UML-SEQ-02 | ApprovalTask first-approve; live next stage; Comment decision; BR-21/25 |
| UML-SEQ-03 | live config; caveat in-flight ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)) |
| UML-UC-01 | покрытие актёров через Role |

---

## 7. Architecture modules → сущности

| Module | Owns / reads |
| :--- | :--- |
| Auth / Authorization | User, Role |
| Cabinet | User profile; Notification (**Future / backlog**) |
| Catalog | RequestType, RequestFieldDefinition (active) |
| Request | Request, RequestFieldValue, Comment |
| Submit Orchestrator | оркестрация → ApprovalTask + Audit (+ Notification **Future / backlog**) |
| Action Engine | ProcessTransition; available_actions; approve_advance |
| Approval Engine | ApprovalTask; reads live ApprovalStage / StageAssignment |
| Admin Config | live config entities | Future / backlog |
| Audit | HistoryEvent |
| Notification | Notification (**Future / backlog**) |
| Persistence | все выше в одной PostgreSQL |

**Удалено:** Snapshot Module.

---

## 8. RBAC / ACL → данные

| Правило | Данные |
| :--- | :--- |
| ACL employee own requests | Request.initiator_user_id |
| ACL approver via tasks | ApprovalTask.assignee_user_id |
| ACL admin all | Role.code=admin |
| Hidden/foreign → 404 | AuthZ поверх тех же ключей (NFR-SEC-05) |
| Admin не создаёт заявки | отсутствие обходного initiator override |

---

## 9. Live config invariants

| Инвариант | Entity / relation |
| :--- | :--- |
| Submit reads live route | ApprovalRoute → ApprovalStage → StageAssignment |
| Task on live stage | ApprovalTask.stage_id FK → ApprovalStage |
| Current stage | Request.current_stage_id FK → ApprovalStage |
| Resubmit from stage 1 | current_stage_id → first ApprovalStage by sequence_no |
| Config change caveat | Admin edits live entities; in-flight may be affected ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)) |
| History without full payload | HistoryEvent.action/from/to/comment only |

---

## 10. Границы трассировки

- Не трассируются будущие OpenAPI paths.
- Snapshot-сущности (RouteInstance*, FieldValueVersion) — **deprecated**; не трассируются.
- Technical logs намеренно вне матрицы сущностей.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия ERD traceability |
| 1.1 | 2026-09-23 | Live config; удалены snapshot entity rows; Action Engine |
