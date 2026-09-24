# ERD-00 — Описание модели данных

**Продукт:** Employee Service  
**ID:** ERD-00  
**Версия:** 2.0  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [README.md](./README.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [erd-domain-model.md](./erd-domain-model.md)

---

## 1. Назначение

Концептуальная и логическая модель данных Employee Service — мост между Vision / требованиями, BPMN / UML / Architecture и будущим API / PostgreSQL.

---

## 2. Уровни модели

| Уровень | Что включает ERD | Что исключено |
| :--- | :--- | :--- |
| **Conceptual** | Сущности, смысл, связи | Реализация |
| **Logical** | Атрибуты, кардинальности, инварианты | PostgreSQL DDL |
| **Physical** | — | Миграции (последующие этапы) |

---

## 3. Классификация сущностей

| Класс | Назначение | Сущности |
| :--- | :--- | :--- |
| **Организация** | Оргструктура | Company, Department, Employee |
| **Identity / RBAC** | Учёт и роли | User, Role (одна роль на User) |
| **Конфигурация процесса** | Live-настройки | Process, Status, Action, ProcessTransition, RequestType, RequestFieldDefinition, ApprovalRoute, ApprovalStage, StageAssignment, Dictionary* |
| **Runtime** | Исполнение заявки | Request (`status_id`, `current_stage_id`), RequestFieldValue, ApprovalTask (`stage_id`) |
| **Аудит** | История и комментарии | HistoryEvent, Comment |
| **Уведомления** | In-app persistence + list | Notification (**Target** create+list; mark-as-read — backlog) |

**Нет класса Snapshot.** Устаревшие сущности (`RouteInstance*`, `FieldValueVersion`) — см. deprecated [snapshot-model.md](./snapshot-model.md).

---

## 4. Границы модулей → данные

| Модуль | Зона данных |
| :--- | :--- |
| Auth / Authorization | User, Role |
| Org | Company, Department, Employee |
| Catalog / Admin Config | Process*, RequestType, fields, Route/Stage/Assignment, Dictionary*, ProcessTransition |
| Request | Request, RequestFieldValue, Comment |
| Action Engine | ProcessTransition (live), available_actions / execute |
| Approval Engine | ApprovalTask (читает **live** stages/assignments) |
| Audit | HistoryEvent |
| Notification | Notification (**Target** create+list; mark-as-read — backlog) |

Транзакции submit/approve/…: status + tasks + audit + Notification в одной БД-транзакции; без outbox/очередей.

---

## 5. Что намеренно не моделируется

| Тема | Причина |
| :--- | :--- |
| RouteInstance / FieldValueVersion | ADR-LIVE-CFG-01 — отказ от snapshot |
| Process versioning | Out of scope |
| Auto-routing по manager | Out of scope; BR-12 |
| BPM engine / Kafka / микросервисы | Out of scope |
| Attachments, email/push | Out of scope Vision |
| Optimistic locking | Не входит в текущий scope |

---

## 6. Связанные артефакты

- [erd-domain-model.md](./erd-domain-model.md)
- [data-dictionary.md](./data-dictionary.md)
- [erd-traceability.md](./erd-traceability.md)
- [snapshot-model.md](./snapshot-model.md) — Deprecated

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия со snapshot |
| 2.0 | 2026-09-23 | Live config; org; process catalogs; без snapshot |
