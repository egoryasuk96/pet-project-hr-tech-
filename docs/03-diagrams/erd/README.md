# ERD + Data Dictionary

**Продукт:** Employee Service  
**ID:** ERD-00-INDEX  
**Версия:** 2.0  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [Vision](../../01-vision-and-scope/vision-scope.md), [Business Rules](../../02-requirements/business-rules.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [Architecture](../architecture/architecture-description.md)

---

## 1. Назначение

Аналитическая модель данных Employee Service: сущности, атрибуты, связи, инварианты **live configuration**, data dictionary и трассировка.

Это **не** физическая схема PostgreSQL, **не** SQL-миграции и **не** runtime-код.

---

## 2. Артефакты

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ERD-00 | [erd-description.md](./erd-description.md) | Индекс раздела, классификация сущностей |
| ERD-DM | [erd-domain-model.md](./erd-domain-model.md) | Mermaid ER — **актуальная** модель |
| ERD-SNAP | [snapshot-model.md](./snapshot-model.md) | **Deprecated** — историческая справка |
| ERD-DD | [data-dictionary.md](./data-dictionary.md) | Словарь сущностей и полей |
| ERD-MAP | [erd-traceability.md](./erd-traceability.md) | Трассировка → сущности |

---

## 3. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; Mermaid `erDiagram` |
| **Конфиг** | Live: ApprovalRoute* + ProcessTransition ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)) |
| **Snapshot** | Не используется; ERD-SNAP только deprecated |
| **ID** | Целевые типы — [ADR-ID-01](../architecture/adr-id-strategy.md) |

---

## 4. Live config (кратко)

| Механизм | Поведение |
| :--- | :--- |
| ApprovalRoute / Stage / Assignment | Читаются при submit и approve_advance |
| ProcessTransition | Читаются при `available_actions` и execute action |
| Request.current_stage_id | FK на live ApprovalStage |
| ApprovalTask.stage_id | FK на live ApprovalStage |

Изменение активной конфигурации может затронуть незавершённые заявки. Process versioning / snapshot — **out of scope**.

---

## 5. Связанные ADR

- [ADR-LIVE-CFG-01](../architecture/adr-live-config.md)
- [ADR-ACTION-01](../architecture/adr-configurable-actions.md)
- [ADR-ORG-01](../architecture/adr-org-model.md)
- [ADR-ID-01](../architecture/adr-id-strategy.md)
- [ADR-SNAP-01](../architecture/adr-snapshot-submit-versions.md) — Superseded

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.1 | 2026-09-20 | Вариант B snapshot |
| 2.0 | 2026-09-23 | Live config; snapshot deprecated |
