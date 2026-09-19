# UML-SM-01 — State Machine: статус заявки

**Проект:** Employee Service  
**Тип диаграммы:** State Machine  
**Файл индекса:** [uml-description.md](./uml-description.md)  
**Связь с BPMN:** справочная схема в [BPMN-01 §8](../bpmn/to-be-request-lifecycle.md) — здесь основная UML-модель состояний

---

## 1. Назначение

Формальная модель жизненного цикла заявки по статусам MVP. Переходы и guard-условия взяты из глоссария и BR; новые статусы и правила **не добавляются**.

---

## 2. Объект

**Контекст:** экземпляр заявки (`Request`).

**Атрибуты состояния (уровень анализа):** `status`, признак текущего этапа (для `in_approval` / после `return`), наличие route snapshot и schema/value snapshot.

---

## 3. Состояния

| Состояние | Смысл | Допустимые действия инициатора |
| :--- | :--- | :--- |
| `draft` | Черновик; не на согласовании | edit, submit, cancel |
| `in_approval` | На согласовании по route snapshot | свободный комментарий (BR-28); cancel **запрещён** |
| `returned` | Возвращена на доработку; номер этапа сохранён | edit, resubmit, cancel |
| `approved` | Финальное согласование | терминальное |
| `rejected` | Отклонена | терминальное |
| `cancelled` | Отменена инициатором | терминальное |

---

## 4. Переходы

| From | To | Событие / действие | Guard | Effect (существующие BR) |
| :--- | :--- | :--- | :--- | :--- |
| `[начальное]` | `draft` | create | тип активен (BR-10) | инициатор = текущий пользователь (BR-19) |
| `draft` | `in_approval` | submit | поля OK (BR-26); маршрут валиден (BR-18); тип активен | **route snapshot** (BR-08) + **schema/value snapshot** (BR-26); задачи 1-го этапа; история; уведомления (BR-29) |
| `draft` | `cancelled` | cancel | — | история (BR-07) |
| `in_approval` | `approved` | finalApprove | approve на последнем этапе snapshot (BR-17) | закрытие задач; уведомление инициатору |
| `in_approval` | `rejected` | reject | комментарий непустой (BR-25); не инициатор (BR-21); своя открытая задача (BR-15) | закрытие открытых задач этапа (BR-04) |
| `in_approval` | `returned` | return | комментарий непустой (BR-25); BR-21; BR-15 | сохранить номер этапа; закрыть задачи этапа (BR-05) |
| `returned` | `in_approval` | resubmit | поля OK по актуальной схеме; маршрут валиден; тип активен | **route snapshot не менять** (BR-22); **обновить** schema/value snapshot (BR-26); задачи **того же** этапа (BR-06) |
| `returned` | `cancelled` | cancel | — | история (BR-07) |

### 4.1. Отклонённые / невозможные переходы (notes)

| Попытка | Результат | Правило |
| :--- | :--- | :--- |
| cancel из `in_approval` / `approved` / `rejected` / `cancelled` | ERR_INVALID_STATE | BR-07 |
| submit из иного статуса, чем `draft`/`returned` | ERR_INVALID_STATE | BR-20 |
| reject/return без комментария | ERR_VALIDATION; статус без изменений | BR-25 |
| approve/reject/return инициатором по своей заявке | ERR_FORBIDDEN_APPROVAL | BR-21 |

Промежуточный «переход этапа» при approve непоследнего этапа **не меняет** `status`: заявка остаётся `in_approval` (BR-02, FR-APP-06).

---

## 5. Диаграмма (Mermaid)

```mermaid
stateDiagram-v2
  [*] --> draft: create

  draft --> in_approval: submit\n[fieldsOK and routeValid]\n/ routeSnapshot + schemaSnapshot + tasks
  draft --> cancelled: cancel

  in_approval --> approved: finalApprove\n[lastStage]
  in_approval --> rejected: reject\n[commentRequired and notInitiator]
  in_approval --> returned: return\n[commentRequired and notInitiator]\n/ keepStageNumber

  returned --> in_approval: resubmit\n[fieldsOK and routeValid]\n/ keepRouteSnapshot + refreshSchemaSnapshot + sameStageTasks
  returned --> cancelled: cancel

  approved --> [*]
  rejected --> [*]
  cancelled --> [*]

  note right of in_approval
    Approve непоследнего этапа:
    status остаётся in_approval
    (BR-02, FR-APP-06)
  end note

  note right of returned
    Dual snapshot:
    route — без изменений (BR-22)
    schema/value — обновляется (BR-26)
  end note
```

---

## 6. Связь с dual snapshot

| Момент | Route snapshot | Schema/value snapshot |
| :--- | :--- | :--- |
| Первый `draft → in_approval` | Создаётся | Создаётся |
| `returned → in_approval` | Без изменений | Обновляется |
| Пока `in_approval` | Только читается при переходах этапов | Фиксированные данные для согласующих |
| Конфиг admin после submit | Не меняет snapshot заявки (BR-09) | Не переписывает in-flight данные до returned-edit/resubmit (BR-26) |

---

## 7. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-04, UC-05, UC-08, UC-09, UC-10 |
| **FR** | FR-REQ-01, FR-REQ-03, FR-REQ-07, FR-REQ-08, FR-REQ-09; FR-APP-04, FR-APP-05, FR-APP-06, FR-APP-07 |
| **BR** | BR-04, BR-05, BR-06, BR-07, BR-08, BR-17, BR-18, BR-19, BR-20, BR-21, BR-22, BR-25, BR-26, BR-29 |
| **AC** | AC-APP-01, AC-APP-02, AC-APP-05b, AC-APP-06, AC-APP-07, AC-APP-08, AC-REQ-07, AC-DRAFT-01, AC-DRAFT-02 |
| **BPMN** | BPMN-01 (жизненный цикл), BPMN-02 (исходы этапа) |

---

## 8. Границы

- Статусы **задачи** согласования (`open` / `completed` / `cancelled`) — на UML-CL-01 и UML-SEQ-02, не отдельные состояния заявки.
- Новые статусы заявки не вводятся.
