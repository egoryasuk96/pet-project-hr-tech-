# Stage 3.4 — ERD + Data Dictionary

**Продукт:** Employee Service  
**ID:** ERD-00-INDEX  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [Vision](../../01-vision-and-scope/vision-scope.md), [Business Rules](../../02-requirements/business-rules.md), [Snapshot Model](./snapshot-model.md), [Architecture](../architecture/architecture-description.md)

---

## 1. Назначение

Аналитическая модель данных Employee Service: сущности, атрибуты, связи, кардинальности, инварианты RouteInstance / FieldValueVersion, data dictionary и трассировка к требованиям.

Это **не** физическая схема PostgreSQL, **не** SQL-миграции и **не** Stage OpenAPI.

---

## 2. Артефакты

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ERD-00 | [erd-description.md](./erd-description.md) | Индекс этапа, уровни модели, классификация сущностей |
| ERD-DM | [erd-domain-model.md](./erd-domain-model.md) | Mermaid ER-диаграмма, кардинальности |
| ERD-SNAP | [snapshot-model.md](./snapshot-model.md) | **Канон:** RouteInstance + FieldValueVersion (вариант B) |
| ERD-DD | [data-dictionary.md](./data-dictionary.md) | Словарь сущностей и полей |
| ERD-MAP | [erd-traceability.md](./erd-traceability.md) | Трассировка → сущности |

---

## 3. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; визуал — Mermaid `erDiagram` |
| **Язык** | Русский (имена сущностей — English PascalCase) |
| **Уровень** | Conceptual + logical; без PostgreSQL DDL |
| **Новые BR** | Не вводятся |
| **Snapshot** | Полная механика **только** в [snapshot-model.md](./snapshot-model.md) |

---

## 4. Snapshot (кратко)

| Механизм | Когда | При resubmit |
| :--- | :--- | :--- |
| **RouteInstance** | Первый successful submit | Без изменений |
| **FieldValueVersion** | Каждый successful submit (номер отправки) | Новая версия; прошлые в истории |

Детали (в т.ч. resubmit с первого этапа, OQ-B): [snapshot-model.md](./snapshot-model.md).

---

## 5. Связанные артефакты

- [Vision & Scope](../../01-vision-and-scope/vision-scope.md)
- [Глоссарий](../../01-vision-and-scope/glossary.md)
- [business-rules.md](../../02-requirements/business-rules.md)
- [Architecture](../architecture/architecture-description.md)
- [ADR-SNAP-01](../architecture/adr-snapshot-submit-versions.md)

---

## 6. Критерии готовности (DoD)

1. Каталог содержит ERD-00…ERD-MAP.
2. Snapshot Model документирует вариант B.
3. Data Dictionary на логическом уровне с ссылками на FR/BR.
4. Нет SQL, миграций, OpenAPI, кода.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Stage 3.4 |
| 1.1 | 2026-09-20 | Вариант B; краткая сводка вместо dual snapshot essay |
