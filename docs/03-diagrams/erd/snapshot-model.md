# ERD-SNAP — Snapshot Model (DEPRECATED)

**Продукт:** Employee Service  
**ID:** ERD-SNAP  
**Версия:** 1.3  
**Статус:** **Deprecated** — не является актуальной моделью  
**Замена:** [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [ERD Domain Model](./erd-domain-model.md)

> Документ сохранён только как историческая справка Baseline (вариант B).  
> **Не проектировать и не реализовывать** `RouteInstance*`, `FieldValueVersion`.

---

## Почему deprecated

Snapshot существенно усложнял ERD и workflow для pet-project. Актуальная архитектура использует **live configuration**:

- `ApprovalRoute` / `ApprovalStage` / `StageAssignment`
- `ProcessTransition`
- `Request.status_id`, `Request.current_stage_id`
- `ApprovalTask.stage_id` → live stage

Ограничение: изменение активной конфигурации может затронуть незавершённые заявки. Версионирование процессов и snapshot — **out of scope**.

---

## Историческое содержание (кратко, не применять)

Ранее: RouteInstance create-once на first submit; FieldValueVersion на каждый submit; resubmit с этапа 1 без rebuild маршрута (OQ-B). Полный текст механики изъят из актуального канона — см. git history при необходимости.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.2 | 2026-09-20 | Вариант B + OQ-B (Baseline) |
| 1.3 | 2026-09-23 | **Deprecated**; ссылка на ADR-LIVE-CFG-01 |
