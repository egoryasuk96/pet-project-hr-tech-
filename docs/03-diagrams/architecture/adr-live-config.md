# ADR — Live configuration (отказ от snapshot)

**Продукт:** Employee Service  
**ID:** ADR-LIVE-CFG-01  
**Версия:** 1.0  
**Статус:** Accepted  
**Связанные документы:** [Vision](../../01-vision-and-scope/vision-scope.md), [Business Rules](../../02-requirements/business-rules.md), [ERD Domain Model](../erd/erd-domain-model.md), [ADR-ACTION-01](./adr-configurable-actions.md), superseded [ADR-SNAP-01](./adr-snapshot-submit-versions.md)

---

## Контекст

Ранее Baseline фиксировал маршрут и значения полей заявки через snapshot-сущности (`RouteInstance*`, `FieldValueVersion`) при submit (вариант B, ADR-SNAP-01). Для pet-project это усложняло ERD, сервисы и трассировку, не давая необходимой ценности: версионирование процессов и изоляция in-flight заявок от правок админки не входят в цели портфолио.

Нужно упростить модель, сохранив последовательный маршрут, first-approve и configurable transitions.

---

## Решение

1. **Snapshot-модель удалена.** Сущности `RouteInstance`, `RouteInstanceStage`, `RouteInstanceAssignment`, `FieldValueVersion` **не** входят в актуальную архитектуру.
2. **Live configuration:** `ApprovalRoute` / `ApprovalStage` / `StageAssignment` и `ProcessTransition` читаются в runtime при submit, approve_advance и расчёте `available_actions`.
3. **Request** хранит `status_id` и `current_stage_id` (FK на live `ApprovalStage`, nullable вне согласования).
4. **ApprovalTask** ссылается на live `stage_id` и `assignee_user_id`; не ссылается на версии значений.
5. Значения полей — только working `RequestFieldValue`. Аудит — `HistoryEvent` и `Comment`.

### Осознанное ограничение (принято)

Изменение активной конфигурации процесса (этапы, назначения, transitions, схема полей) **может затронуть ещё не завершённые заявки**.

**Out of scope:** версионирование процессов (process versioning), snapshot конфигурации/маршрута/значений, event sourcing, отдельный workflow engine.

Рекомендуемое простое правило админки (BR): не удалять этап, на который есть open tasks или заявки в `in_approval` с этим `current_stage_id`.

---

## Последствия

| + | − |
| :--- | :--- |
| Проще ERD и Approval Engine | Нет изоляции in-flight от правок конфига |
| Один источник истины для маршрута | Нужны admin-ограничения на опасные правки |
| Согласовано с configurable ProcessTransition | История «какой маршрут был» только через HistoryEvent |

---

## Supersedes

- [ADR-SNAP-01](./adr-snapshot-submit-versions.md) — статус **Superseded**
- [Snapshot Model](../erd/snapshot-model.md) — статус **Deprecated**

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-23 | Принят отказ от snapshot; live config |
