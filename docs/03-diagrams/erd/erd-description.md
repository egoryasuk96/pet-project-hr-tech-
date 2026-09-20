# ERD-00 — Описание модели данных (Stage 3.4)

**Проект:** Employee Service  
**Этап:** 3.4 — ERD + Data Dictionary  
**Версия:** 1.0  
**Статус:** Draft  
**Индекс:** [README.md](./README.md)

---

## 1. Назначение

Зафиксировать **концептуальную и логическую** модель данных Employee Service как мост между:

- глоссарием и требованиями (Stage 1–2);
- BPMN / UML / Architecture (Stage 3.1–3.3);
- будущим проектированием API и PostgreSQL (этапы после 3.4).

Модель должна быть достаточно детальной для следующего этапа (API), но **не** превращаться в физическую схему БД раньше времени.

---

## 2. Уровни модели

| Уровень | Что включает Stage 3.4 | Что исключено |
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
| **Snapshot / historical** | Замороженные копии и прикладной аудит | RouteSnapshot, RouteSnapshotStage, RouteSnapshotAssignment, SchemaValueSnapshot, HistoryEvent |
| **Технические** | RBAC, credentials, флаги доставки | Role, UserRole, User.passwordHash, Notification |

Одна сущность может участвовать в нескольких классах (например, Request — бизнес + runtime). Классификация нужна, чтобы не смешивать **live config**, **working values** и **frozen snapshots**.

---

## 4. Границы модулей → данные (без микросервисов)

Архитектура — **modular monolith + одна PostgreSQL**. Логические модули владеют зонами данных, но не отдельными БД:

| Модуль (Architecture) | Зона данных |
| :--- | :--- |
| Auth / Authorization | User, Role, UserRole |
| Catalog / Admin Config | RequestType, FieldDefinition, Route/Stage/Assignment, Dictionary* |
| Request | Request, RequestFieldValue, Comment |
| Snapshot | RouteSnapshot*, SchemaValueSnapshot |
| Approval Engine | ApprovalTask (читает RouteSnapshot) |
| Audit | HistoryEvent |
| Notification | Notification |

Транзакционные границы submit/approve (status + snapshots/tasks + audit + notifications) заданы Architecture ADR-TX-* и BR-29 / NFR-REL-01; ERD обеспечивает сущности для этих границ, не вводя очереди/outbox.

---

## 5. Что намеренно не моделируется

| Тема | Причина |
| :--- | :--- |
| SubmitVersion / RequestVersion | Требования не требуют полного payload всех прошлых submit; HistoryEvent фиксирует факт события |
| Оргструктура / дерево руководителей | Out of scope; BR-12 — явные назначения |
| Attachments, email/push | Out of scope Vision |
| JWT / refresh sessions на сервере | Stateless JWT (NFR-SCL-01, NFR-SEC-04) |
| Technical API logs | NFR-LOG-01; retention 14 дней (NFR-LOG-03 п.1); infra, не предметная ERD |
| Optimistic locking / version columns | Не входит в MVP |
| Параллельные этапы маршрута | Out of scope |
| Физические индексы, soft-delete стратегии | Этап реализации / DDL |

---

## 6. Legacy PNG

[`ERD (pet-project-hr-tech).png`](./ERD%20(pet-project-hr-tech).png) — **obsolete**. Оставлен на месте без переименования и перемещения. Актуальная модель — Markdown Stage 3.4.

---

## 7. Связанные артефакты этапа

- [erd-domain-model.md](./erd-domain-model.md)
- [snapshot-model.md](./snapshot-model.md)
- [data-dictionary.md](./data-dictionary.md)
- [erd-traceability.md](./erd-traceability.md)

---

## 8. Критерии готовности (DoD)

См. [README.md §7](./README.md).

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия ERD-00 |
