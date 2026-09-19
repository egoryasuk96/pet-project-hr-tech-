# ERD-SNAP — Snapshot Model (dual snapshot)

**Проект:** Employee Service  
**Этап:** 3.4  
**Версия:** 1.0  
**Статус:** Draft  
**Индекс:** [README.md](./README.md)

---

## 1. Назначение

Зафиксировать два **разных** snapshot-механизма Employee Service и их связь с `Request`, без введения сущности SubmitVersion / RequestVersion.

Новые бизнес-правила **не** добавляются. Источники: BR-08, BR-09, BR-22, BR-26; BPMN-01; UML-SEQ-01 / UML-CL-01; Architecture Snapshot Module.

---

## 2. Два механизма

| | **RouteSnapshot** | **SchemaValueSnapshot** |
| :--- | :--- | :--- |
| **Что фиксирует** | Этапы, порядок, назначения маршрута | Схему полей + значения полей заявки |
| **Когда создаётся** | Только при **первом** successful submit из `draft` (BR-08) | При **каждом** successful submit — первом и resubmit (BR-26) |
| **При return** | Не меняется | Не меняется (заявка в `returned`; working values редактируются отдельно) |
| **При resubmit** | **Сохраняется** (BR-22) | **Current заменяется** новым successful snapshot (BR-22) |
| **Immutability** | Write-once | Нет in-place patch между submit; только атомарная замена current при следующем successful submit |
| **Кто читает** | Approval Engine (задачи, next stage) | Согласующие / карточка в workflow (frozen данные) |
| **Кардинальность** | Request **1 — 0..1** | Request **1 — 0..1 current** |

**SubmitVersion / RequestVersion в MVP нет:** требования не обязывают хранить полный payload всех предыдущих submit. Факт submit/resubmit пишет **HistoryEvent** (без полного snapshot payload).

---

## 3. Связь Request → snapshots

```text
Request (draft)
  ├── RequestFieldValue          ← working values (live schema, BR-26)
  ├── RouteSnapshot              = отсутствует
  └── SchemaValueSnapshot        = отсутствует

Request (после первого successful submit)
  ├── RequestFieldValue          ← могут оставаться / синхронизироваться с последним submit
  ├── RouteSnapshot              = 1 (immutable)
  │     ├── RouteSnapshotStage[]
  │     └── RouteSnapshotAssignment[]
  └── SchemaValueSnapshot        = 1 current (frozen schema + values)

Request (returned → edit)
  ├── RequestFieldValue          ← мутации по live schema типа
  ├── RouteSnapshot              = тот же (не трогать)
  └── SchemaValueSnapshot        = прежний current (для истории просмотра до resubmit;
                                   согласующие после return не продолжают этап до resubmit)

Request (после successful resubmit)
  ├── RouteSnapshot              = тот же экземпляр
  └── SchemaValueSnapshot        = новый current (предыдущий current заменён)
```

### 3.1. Кардинальности (обязательные)

| Связь | Кардинальность | Обязательность |
| :--- | :--- | :--- |
| Request → RouteSnapshot | **1 — 0..1** | Отсутствует до первого successful submit; после — ровно один |
| Request → SchemaValueSnapshot (current) | **1 — 0..1** | Отсутствует до первого successful submit; после — ровно один current |
| RouteSnapshot → RouteSnapshotStage | 1 — 1..N | После создания: ≥1 stage (иначе submit был бы отклонён BR-18) |
| RouteSnapshotStage → RouteSnapshotAssignment | 1 — 1..N | ≥1 assignment на stage (BR-18) |

---

## 4. Жизненный цикл (timeline)

```mermaid
sequenceDiagram
  participant Init as Initiator
  participant Req as Request
  participant WV as RequestFieldValue
  participant RS as RouteSnapshot
  participant SV as SchemaValueSnapshot
  participant HE as HistoryEvent

  Init->>Req: create draft
  Init->>WV: edit values (live schema)
  Init->>Req: first successful submit
  Req->>RS: create write-once
  Req->>SV: create current
  Req->>HE: submit event (no full payload)
  Note over RS: immutable forever for this Request

  Note over Req: return → status returned; RS unchanged
  Init->>WV: edit values (live schema)
  Init->>Req: successful resubmit
  Note over RS: keep existing
  Req->>SV: replace current with new snapshot
  Req->>HE: resubmit event (no full payload)
```

---

## 5. Working values vs frozen values

| Хранилище | Статусы записи | Схема валидации | Назначение |
| :--- | :--- | :--- | :--- |
| **RequestFieldValue** | `draft`, `returned` (и сохранение до/между submit) | **Актуальная** live schema типа (BR-26) | Редактирование инициатором |
| **SchemaValueSnapshot** | Создаётся/заменяется только на successful submit | Копия схемы + значений **на момент** submit | Просмотр в workflow; изоляция от смены admin-схемы до следующего returned-edit/resubmit |

После successful submit согласующие опираются на **SchemaValueSnapshot**, а не на live FieldDefinition.

---

## 6. Route snapshot и задачи

1. При submit/resubmit Approval Engine **не** читает live `StageAssignment` для in-flight заявки.
2. Задачи (`ApprovalTask`) материализуются из **RouteSnapshotAssignment** текущего этапа (`currentStageNumber`).
3. Назначение по роли в snapshot раскрывается в задачи на конкретных User на момент создания задач; в snapshot сохраняется и роль/user для трассировки конфигурации на момент first submit.
4. Изменение admin-конфига маршрута **не** меняет существующий RouteSnapshot (BR-09).

---

## 7. Immutability (логический уровень)

| Правило | Смысл |
| :--- | :--- |
| RouteSnapshot write-once | После create запрещены UPDATE содержимого stages/assignments |
| SchemaValueSnapshot no patch | Запрещено частично менять schemaDocument/valuesDocument «на лету» |
| Replace on resubmit | Допускается только атомарная замена **current** SchemaValueSnapshot при successful resubmit |
| Нет optimistic locking | Версионирование строк / `ERR_CONFLICT_VERSION` вне MVP |

Физический способ замены current (UPDATE vs delete+insert) — решение этапа реализации; на ERD достаточно семантики «один current».

---

## 8. HistoryEvent и snapshot

- HistoryEvent фиксирует **значимые действия** (BR-24), включая submit / resubmit.
- HistoryEvent **не обязан** хранить полный payload RouteSnapshot или SchemaValueSnapshot.
- Retention прикладной истории: **60 дней** — NFR-LOG-03 п.2 (см. также NFR-LOG-02).
- Technical API logs (14 дней, NFR-LOG-03 п.1) — **не** HistoryEvent и не часть этой модели.

---

## 9. Согласованность с артефактами

| Источник | Ожидание | Вердикт |
| :--- | :--- | :--- |
| BR-08 | Route snapshot при первом submit | Соответствует |
| BR-09 | Конфиг не ретроактивен к snapshot | Соответствует |
| BR-22 | Route не пересоздаётся; schema/values обновляются | Соответствует (замена current) |
| BR-26 | Live при edit; freeze после submit | Соответствует |
| BPMN-01 §3 | Dual snapshot table | Соответствует |
| UML-SEQ-01 | First create both; resubmit keep route / update schema | Соответствует |
| UML-CL-01 | 1—0..1 Route; 1—0..1 SchemaValue | Соответствует |
| Architecture Snapshot Module | create-once route; upsert schema/value | Соответствует (семантика current) |

**Реальных противоречий нет.** Нюанс терминов «обновляется» / «upsert» / «заменяется» — одна аналитическая семантика без SubmitVersion.

---

## 10. Границы

- Нет сущности SubmitVersion / RequestVersion.
- Нет хранения полной цепочки прошлых SchemaValueSnapshot как требования MVP.
- Нет физической DDL-семантики JSON.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Snapshot Model Stage 3.4 |
