# ERD-00 — Описание модели данных

**Продукт:** Employee Service  
**ID:** ERD-00  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [README.md](./README.md), [Snapshot Model](./snapshot-model.md)

---

## 1. Назначение

Зафиксировать **концептуальную и логическую** модель данных Employee Service как мост между:

- глоссарием и требованиями (Vision / требования);
- BPMN / UML / Architecture;
- будущим проектированием API и PostgreSQL (после Baseline).

Модель должна быть достаточно детальной для будущего контракта API, но **не** превращаться в физическую схему БД раньше времени.

---

## 2. Уровни модели

| Уровень | Что включает ERD | Что исключено |
| :--- | :--- | :--- |
| **Conceptual** | Сущности предметной области, смысл, связи | Реализация |
| **Logical** | Атрибуты, логические типы, кардинальности, обязательность, ограничения целостности, enum-статусы | PostgreSQL DDL, индексы, партиции |
| **Physical** | — | Миграции, `jsonb` vs `text`, PK-стратегии СУБД |

Логический тип `JSON` в Data Dictionary означает «структурированный документ на уровне анализа», а не выбор `jsonb` в PostgreSQL.

---

## 3. Классификация сущностей

| Класс | Назначение | Сущности |
| :--- | :--- | :--- |
| **Бизнес** | Предметные объекты пользователя | User (профиль), Request, Comment, ApprovalTask |
| **Конфигурация** | Live-настройки admin (каталог, маршрут, справочники) | RequestType, RequestFieldDefinition, ApprovalRoute, ApprovalStage, StageAssignment, Dictionary, DictionaryItem |
| **Runtime** | Состояние исполнения заявки | Request (status, currentStageNumber), RequestFieldValue, ApprovalTask |
| **Snapshot / historical** | Замороженные копии и прикладной аудит | RouteInstance, RouteInstanceStage, RouteInstanceAssignment, FieldValueVersion, HistoryEvent |
| **Технические** | RBAC, credentials; Notification (**Future / backlog**) | Role, UserRole, User.passwordHash, Notification |

Одна сущность может участвовать в нескольких классах (например, Request — бизнес + runtime). Классификация нужна, чтобы не смешивать **live config**, **working values** и **frozen snapshots**.

---

## 4. Границы модулей → данные (без микросервисов)

Архитектура — **modular monolith + одна PostgreSQL**. Логические модули владеют зонами данных, но не отдельными БД:

| Модуль (Architecture) | Зона данных |
| :--- | :--- |
| Auth / Authorization | User, Role, UserRole |
| Catalog / Admin Config | RequestType, FieldDefinition, Route/Stage/Assignment, Dictionary* |
| Request | Request, RequestFieldValue, Comment |
| Snapshot | RouteInstance*, FieldValueVersion |
| Approval Engine | ApprovalTask (читает RouteInstance) |
| Audit | HistoryEvent |
| Notification | Notification (**Future / backlog**) |

Транзакционные границы submit/approve (status + snapshots/tasks + audit; + notifications **Future / backlog** при BR-29) заданы Architecture ADR-TX-* и NFR-REL-01; ERD обеспечивает сущности для этих границ, не вводя очереди/outbox.

---

## 5. Что намеренно не моделируется

| Тема | Причина |
| :--- | :--- |
| Версии значений | **FieldValueVersion** по номеру submit; канон — [snapshot-model.md](./snapshot-model.md) |
| Оргструктура / дерево руководителей | Out of scope; BR-12 — явные назначения |
| Attachments, email/push | Out of scope Vision |
| JWT / refresh sessions на сервере | Полная auth/JWT — **Future / backlog**; Baseline demo-auth не требует session entities |
| Technical API logs | NFR-LOG-01; retention 14 дней (NFR-LOG-03 п.1); infra, не предметная ERD |
| Optimistic locking / version columns | Не входит в MVP |
| Параллельные этапы маршрута | Out of scope |
| Физические индексы, soft-delete стратегии | Этап реализации / DDL |

---

## 6. Связанные артефакты раздела

- [erd-domain-model.md](./erd-domain-model.md)
- [snapshot-model.md](./snapshot-model.md)
- [data-dictionary.md](./data-dictionary.md)
- [erd-traceability.md](./erd-traceability.md)

---

## 7. Критерии готовности (DoD)

См. [README.md §6](./README.md).

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия ERD-00 |
