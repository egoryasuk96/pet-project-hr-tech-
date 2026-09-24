# ADR — Snapshot: экземпляр маршрута и версии значений (вариант B)

**Продукт:** Employee Service  
**ID:** ADR-SNAP-01  
**Версия:** 1.2  
**Статус:** **Superseded** by [ADR-LIVE-CFG-01](./adr-live-config.md)  
**Связанные документы:** [Deprecated Snapshot Model](../erd/snapshot-model.md), [ADR-LIVE-CFG-01](./adr-live-config.md)

> **Не использовать как актуальную архитектуру.** Документ сохранён для истории решений Baseline.

---

## Контекст (исторический)

Для согласования фиксировались: (1) маршрут конкретной заявки; (2) значения полей на момент решения. Вариант B + OQ-B.

---

## Решение (историческое, вариант B + OQ-B)

1. **RouteInstance** — один раз при первом submit; при resubmit не пересобирается.
2. **FieldValueVersion** — на каждый successful submit; решение bound to version.
3. После return + resubmit — с первого этапа; новая версия — полный цикл решений.

---

## Почему superseded

Для pet-project snapshot усложнял модель без необходимой ценности. Актуальная архитектура: **live** `ApprovalRoute` / stages / assignments и live `ProcessTransition`; см. [ADR-LIVE-CFG-01](./adr-live-config.md). Process versioning и snapshot — **out of scope**.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Принят вариант B |
| 1.1 | 2026-09-20 | Закрыт OQ-B |
| 1.2 | 2026-09-23 | **Superseded** ADR-LIVE-CFG-01 |
