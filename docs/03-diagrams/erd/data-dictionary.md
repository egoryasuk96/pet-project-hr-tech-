# ERD-DD - Data Dictionary

**Продукт:** Employee Service  
**ID:** ERD-DD  
**Версия:** 2.0  
**Статус:** Target architecture (docs E0-E1)  
**Связанные документы:** [README.md](./README.md), [erd-domain-model.md](./erd-domain-model.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md)

---

## 1. Соглашения

Логический словарь target-модели. Snapshot-сущности удалены ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)).

---

## 2. Request (runtime)

| Field | Type | Required | Nullable | Description | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| status_id | int | yes | no | FK > Status | UML-SM-01 |
| current_stage_id | int | no | yes | FK > ApprovalStage | ADR-LIVE-CFG-01 |
| initiator_user_id | UUID | yes | no | FK > User | BR-19 |

Нет RouteInstance / FieldValueVersion.

---

## 3. RequestFieldValue (working values)

Единственный носитель значений полей (BR-26). Live schema при edit/submit.

---

## 4. ApprovalTask

| Field | Type | Required | Description | Source |
| :--- | :--- | :--- | :--- | :--- |
| stage_id | int | yes | FK > live ApprovalStage | BR-02 |
| assignee_user_id | UUID | yes | FK > User | BR-15 |
| comment | string | no | Decision comment | BR-25 |
| created_at | timestamptz | yes | Immutable | FR-APP-01 |
| completed_at | datetime | no | Completion | FR-APP-03 |

Нет value_version_id.

---

## 5. Live config stubs

Process, Status, Action, ProcessTransition - ADR-ACTION-01.  
Company, Department, Employee - ADR-ORG-01.  
ApprovalRoute, ApprovalStage, StageAssignment - live; in-flight caveat ADR-LIVE-CFG-01.

---

## 6. Deprecated (removed)

| Entity | Replacement |
| :--- | :--- |
| RouteInstance* | Live route + current_stage_id |
| FieldValueVersion | RequestFieldValue + HistoryEvent |

[snapshot-model.md](./snapshot-model.md) - Deprecated.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 2.0 | 2026-09-23 | Live config; snapshot removed |
| 1.1 | 2026-09-21 | ApprovalTask.created_at |
| 1.0 | 2026-09-19 | Первая версия |
