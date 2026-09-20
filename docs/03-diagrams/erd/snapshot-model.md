# ERD-SNAP — Snapshot Model (вариант B)

**Продукт:** Employee Service  
**ID:** ERD-SNAP  
**Версия:** 1.2  
**Статус:** Baseline v1.0  
**Связанные документы:** [ERD README](./README.md), [Business Rules](../../02-requirements/business-rules.md), [ADR: submit versions](../architecture/adr-snapshot-submit-versions.md), [Backlog](../../backlog.md)

---

## 1. Назначение

Каноническое описание механики фиксации маршрута и версий значений полей заявки (продуктовое решение — **вариант B**).  
В остальных документах — только краткая отсылка сюда.

Источники правил: BR-06, BR-08, BR-09, BR-22, BR-26, BR-24; UC-05, UC-14. Новые ID требований **не** вводятся.

---

## 2. Два механизма (кратко)

| | **Экземпляр маршрута (RouteInstance)** | **Версия значений полей (FieldValueVersion)** |
| :--- | :--- | :--- |
| **Что фиксирует** | Набор этапов и назначений **конкретной** заявки; на этапах фиксируются решения | Схему полей + значения на момент данного successful submit |
| **Когда создаётся** | Один раз — при **первом** successful submit из `draft` (BR-08) | При **каждом** successful submit; номер версии = номер отправки (1, 2, …) |
| **При resubmit** | **Не** пересобирается (BR-22) | Создаётся **новая** версия; предыдущие сохраняются |
| **Связь с решением** | Решение согласующего относится к этапу экземпляра маршрута | Решение привязано к **той** FieldValueVersion, которая была актуальна на момент решения |
| **Кто читает** | Approval Engine (задачи, next stage) | Согласующие на текущем этапе — **текущую** версию; история — прошлые версии (BR-24, UC-14) |
| **Кардинальность** | Request **1 — 0..1** | Request **1 — 0..N** (по одной на каждый successful submit) |

Имена `RouteSnapshot` / `SchemaValueSnapshot` в более ранних черновиках соответствуют **RouteInstance** / **FieldValueVersion**; семантика «replace current» **отменена**.

---

## 3. Жизненный цикл

```text
Request (draft)
  ├── RequestFieldValue     ← working values (live schema, BR-26)
  ├── RouteInstance         = нет
  └── FieldValueVersion[]   = пусто

После первого successful submit (submit #1)
  ├── RouteInstance         = создан write-once (этапы + назначения)
  ├── currentStageNumber    = 1
  └── FieldValueVersion #1  = схема + значения на submit #1
      └── решения этапов привязаны к version #1

returned → edit
  ├── RequestFieldValue     ← правки по live schema
  ├── RouteInstance         = тот же
  ├── currentStageNumber    = N этапа return (аудит; не определяет старт resubmit)
  └── FieldValueVersion[]   = без изменений до resubmit
      (прошлые решения остаются на своих версиях)

После successful resubmit (submit #2) — OQ-B / BR-06
  ├── RouteInstance         = тот же (не rebuild)
  ├── currentStageNumber    → 1
  └── FieldValueVersion #2  = новая версия; полный новый цикл решений по этапам
      └── решения по #1 остаются в истории, bound to version #1
```

### 3.1. Кардинальности

| Связь | Кардинальность |
| :--- | :--- |
| Request → RouteInstance | **1 — 0..1** (после первого submit — ровно один) |
| Request → FieldValueVersion | **1 — 0..N** (N = число successful submit) |
| RouteInstance → этапы / назначения | 1 — 1..N / 1 — 1..N (как при submit, BR-18) |
| Решение согласующего → FieldValueVersion | N — 1 (решение bound to value version) |

---

## 4. Resubmit после return (решение OQ-B)

После `return` + successful resubmit:

1. **RouteInstance не пересобирается** (BR-22).
2. Создаётся **новая FieldValueVersion**; у каждой версии — **полный цикл решений** по этапам маршрута.
3. `currentStageNumber` → **1**; создаются задачи **первого** этапа (BR-06).
4. Решения, принятые до return, остаются привязанными к **предыдущей** FieldValueVersion и доступны в истории (BR-24); они не переносятся на новый проход.

Номер этапа, сохранённый при return, используется для аудита (на каком этапе вернули), но **не** задаёт стартовый этап после resubmit.

---

## 5. Immutability

| Правило | Смысл |
| :--- | :--- |
| RouteInstance write-once | После create содержимое этапов/назначений не UPDATE |
| FieldValueVersion append-only | Новая версия только на successful submit; прошлые не переписываются |
| Нет in-place patch версии | Между submit значения версии не правятся «на лету» |
| Конфиг admin | Не меняет RouteInstance уже отправленных заявок (BR-09); в MVP admin UI нет — принцип сохранён для будущего ([backlog](../../backlog.md)) |

---

## 6. История (BR-24 / UC-14)

- Значимые события (submit, resubmit, approve/reject/return, …) пишутся в историю заявки.
- Предыдущие **FieldValueVersion** доступны для просмотра в истории карточки (UC-14): видно, с какими значениями принималось решение.
- Полный payload версии может храниться как документ версии; HistoryEvent не обязан дублировать его целиком, но обязан обеспечивать трассировку «событие ↔ версия».

---

## 7. Согласованность

| Источник | Ожидание при варианте B + OQ-B |
| :--- | :--- |
| BR-06 | Resubmit с первого этапа; полный цикл решений на новой версии |
| BR-08 / BR-09 | RouteInstance once; изоляция; MVP без runtime-смены маршрута → [backlog](../../backlog.md) |
| BR-22 | Route не rebuild; новая FieldValueVersion |
| BR-26 | Live schema при edit; freeze в версии на submit |
| BR-24 / UC-14 | Прошлые версии и решения видны в истории |
| ADR | [adr-snapshot-submit-versions.md](../architecture/adr-snapshot-submit-versions.md) |

---

## 8. Границы

- Нет новых BR/FR/UC/AC ID.
- Физический DDL / JSON-схема хранения — этап реализации.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия (dual snapshot / replace-current) |
| 1.1 | 2026-09-20 | Вариант B: RouteInstance + FieldValueVersion; OQ-A/OQ-B |
| 1.2 | 2026-09-20 | Закрыт OQ-B: resubmit с первого этапа |
