# ADR — Стратегия идентификаторов

**Продукт:** Employee Service  
**ID:** ADR-ID-01  
**Версия:** 1.0  
**Статус:** Accepted (Target-active)  
**Связанные документы:** [ERD Domain Model](../erd/erd-domain-model.md), [ADR-LIVE-CFG-01](./adr-live-config.md)

---

## Контекст

Для портфолио и UI нужны понятные номера заявок («Заявка №10245») и простые справочные ID. UUID оправдан для учётных записей (JWT `sub`). Ранний Baseline с почти всеми PK как UUID — HISTORICAL; Target ниже = CURRENT.

---

## Решение (CURRENT / TARGET)

| Сущность | Тип PK |
| :--- | :--- |
| **User** | UUID |
| Role, Company, Department, Employee, Process, RequestType, Status, Action, ProcessTransition | INTEGER |
| Request | INTEGER (identity, sequence start 10000) — отображается как номер заявки |
| ApprovalRoute, ApprovalStage, StageAssignment, ApprovalTask, RequestField*, Comment, HistoryEvent, Dictionary* | INTEGER |

Отдельное поле `request.number` не вводится: номер заявки = `request.id`.

---

## Последствия

- JWT `sub` остаётся UUID пользователя.
- API и UI справочников используют int id + `code`/`name`.
- Breaking change контракта относительно Baseline UUID — осознанно для рефакторинга.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-23 | Целевая стратегия ID |
| 1.1 | 2026-09-24 | Target = CURRENT; убрано «почти все PK — UUID» |
