# Stage 3.4 — ERD + Data Dictionary

**Проект:** Employee Service  
**Этап:** 3.4 — Conceptual / Logical Data Model  
**Версия:** 1.0  
**Статус:** Draft  
**Источник:** Stage 1–3.3 (`01-vision-and-scope/`, `02-requirements/`, BPMN, UML, Architecture)

---

## 1. Назначение

Аналитическая модель данных Employee Service: сущности, атрибуты, связи, кардинальности, snapshot-инварианты, data dictionary и трассировка к требованиям.

Это **не** физическая схема PostgreSQL, **не** SQL-миграции и **не** Stage 3.5 (API).

---

## 2. Артефакты

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ERD-00 | [erd-description.md](./erd-description.md) | Индекс этапа, уровни модели, классификация сущностей, границы, DoD |
| ERD-DM | [erd-domain-model.md](./erd-domain-model.md) | Mermaid ER-диаграмма, кардинальности, ограничения целостности |
| ERD-SNAP | [snapshot-model.md](./snapshot-model.md) | Dual snapshot: Route vs Schema/Value, immutability, resubmit |
| ERD-DD | [data-dictionary.md](./data-dictionary.md) | Словарь сущностей и полей (логический уровень) |
| ERD-MAP | [erd-traceability.md](./erd-traceability.md) | Трассировка FR / BR / UC / BPMN / UML / Architecture → сущности |

---

## 3. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; визуал — Mermaid `erDiagram` |
| **Язык** | Русский (имена сущностей — English PascalCase, как в UML-CL-01) |
| **Уровень** | Conceptual + logical; без PostgreSQL DDL и индексов |
| **Типы полей** | Логические (`UUID`, `string`, `datetime`, `enum`, `JSON`, …), отдельно от физической реализации |
| **Новые BR** | Не вводятся; модель поддерживает уже зафиксированные правила |
| **SubmitVersion** | **Не** добавляется в MVP |

---

## 4. Dual snapshot (кратко)

| Механизм | Когда | При resubmit |
| :--- | :--- | :--- |
| **RouteSnapshot** | Первый successful submit из `draft` | Сохраняется (immutable) |
| **SchemaValueSnapshot** | Каждый successful submit | Current заменяется новым |

Детали: [snapshot-model.md](./snapshot-model.md).

---

## 5. Связанные артефакты

- [Vision & Scope](../../01-vision-and-scope/vision-scope.md)
- [Глоссарий](../../01-vision-and-scope/glossary.md)
- [business-rules.md](../../02-requirements/business-rules.md)
- [functional-requirements.md](../../02-requirements/functional-requirements.md)
- [BPMN](../bpmn/bpmn-description.md)
- [UML](../uml/uml-description.md)
- [Architecture](../architecture/architecture-description.md)

---

## 6. Критерии готовности (DoD)

1. Каталог содержит ERD-00…ERD-MAP.
2. Mermaid ER покрывает сущности UML-CL-01 + уточнения Stage 3.4 (working values, snapshot children).
3. Snapshot Model документирует Route vs Schema/Value без SubmitVersion.
4. Data Dictionary описывает поля на логическом уровне с ссылками на FR/BR.
5. Traceability связывает сущности с FR/BR/UC/BPMN/UML/ARCH.
6. Нет SQL, миграций, OpenAPI, кода.
7. [docs/README.md](../../README.md) ссылается на Stage 3.4.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Stage 3.4 ERD + Data Dictionary |
