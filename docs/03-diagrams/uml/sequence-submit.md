# UML-SEQ-01 — Sequence: create / submit / resubmit / cancel

**Продукт:** Employee Service  
**ID:** UML-SEQ-01  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [uml-description.md](./uml-description.md), [Snapshot Model](../erd/snapshot-model.md)

---

## 1. Назначение

Взаимодействия инициатора и системы при создании заявки, первом submit, повторном submit после return и отмене. Механика RouteInstance / FieldValueVersion — [Snapshot Model](../erd/snapshot-model.md) (BR-08 / BR-22 / BR-26).

---

## 2. Участники (lifelines)

| Lifeline | Смысл |
| :--- | :--- |
| **Инициатор** | Роль `employee`, владелец заявки |
| **Система** | Граница Employee Service (единый участник анализа) |

### 2.1. Логические области ответственности (не архитектура)

На диаграммах ниже имена **Validation**, **Snapshot**, **TaskFactory**, **Audit**, **Notification** обозначают **логические роли / области ответственности на уровне анализа**.

Они **не** являются:

- микросервисами;
- компонентами целевой архитектуры;
- REST API / модулями реализации.

Это способ показать разделение обязанностей внутри «Системы» при описании сценария.

---

## 3. Основные сценарии

### 3.1. Создание draft и заполнение полей

1. Инициатор создаёт заявку активного типа → статус `draft` (BR-19).
2. Редактирование полей по **актуальной** схеме типа (BR-26).
3. История создания (BR-24).

### 3.2. Первый submit из `draft`

1. Validation: поля по актуальной схеме; маршрут валиден (BR-18); тип активен.
2. Snapshot: создать **RouteInstance** (BR-08).
3. Snapshot: создать **FieldValueVersion** #1 (BR-26).
4. Статус → `in_approval` (BR-20).
5. TaskFactory: задачи первого этапа по RouteInstance.
6. Audit (+ Notification при наличии в scope) в одной транзакции с бизнес-событием.

### 3.3. Resubmit из `returned`

1. Validation: как при submit.
2. Snapshot: **не** rebuild RouteInstance (BR-22).
3. Snapshot: **новая** FieldValueVersion (BR-26, BR-22).
4. Статус → `in_approval`; задачи **того же** этапа (BR-06; OQ — Snapshot Model §6).
5. Audit + Notification (BR-29).

### 3.4. Cancel

- Только из `draft` или `returned` → `cancelled` (BR-07).
- Иной статус → ERR_INVALID_STATE.

### 3.5. Альтернативы / исключения

| Условие | Результат |
| :--- | :--- |
| Ошибка валидации полей | ERR_VALIDATION; статус без изменений |
| Невалидный маршрут | ERR_ROUTE_CONFIG |
| Неактивный тип | ERR_INACTIVE_TYPE |
| Неверный статус для submit/cancel | ERR_INVALID_STATE |

---

## 4. Sequence: первый submit (Mermaid)

```mermaid
sequenceDiagram
  actor Init as Инициатор
  participant Sys as Система
  Note over Sys: Логические области анализа<br/>(не сервисы/API): Validation, Snapshot,<br/>TaskFactory, Audit, Notification

  Init->>Sys: Создать заявку (активный тип)
  Sys-->>Init: draft создан

  Init->>Sys: Сохранить поля (актуальная схема)
  Sys-->>Init: значения сохранены

  Init->>Sys: Submit
  Sys->>Sys: Validation: поля + маршрут + тип активен
  alt Ошибка валидации / маршрута / типа
    Sys-->>Init: ERR_VALIDATION / ERR_ROUTE_CONFIG / ERR_INACTIVE_TYPE
  else OK (первый submit из draft)
    Sys->>Sys: Snapshot: создать RouteInstance (BR-08)
    Sys->>Sys: Snapshot: создать FieldValueVersion (BR-26)
    Sys->>Sys: status = in_approval
    Sys->>Sys: TaskFactory: задачи этапа 1 по RouteInstance
    Sys->>Sys: Audit: событие submit
    Sys->>Sys: Notification: in-app согласующим (та же транзакция, BR-29)
    Sys-->>Init: заявка на согласовании
  end
```

---

## 5. Sequence: resubmit и cancel (Mermaid)

```mermaid
sequenceDiagram
  actor Init as Инициатор
  participant Sys as Система
  Note over Sys: Логические области анализа<br/>(не сервисы/API)

  Note over Init,Sys: Заявка в returned; номер этапа N сохранён

  Init->>Sys: Изменить поля (актуальная схема, BR-26)
  Sys-->>Init: значения сохранены

  Init->>Sys: Resubmit
  Sys->>Sys: Validation: поля + маршрут + тип
  alt Ошибка
    Sys-->>Init: ошибка; статус returned
  else OK
    Sys->>Sys: Snapshot: RouteInstance НЕ менять (BR-22)
    Sys->>Sys: Snapshot: новая FieldValueVersion (BR-26)
    Sys->>Sys: status = in_approval
    Sys->>Sys: TaskFactory: задачи этапа N (BR-06; OQ Snapshot Model §6)
    Sys->>Sys: Audit
    Sys-->>Init: заявка снова in_approval
  end

  Note over Init,Sys: Отмена (альтернатива из draft или returned)

  Init->>Sys: Cancel
  alt status draft или returned
    Sys->>Sys: status = cancelled
    Sys->>Sys: Audit: отмена
    Sys-->>Init: cancelled
  else иной статус
    Sys-->>Init: ERR_INVALID_STATE
  end
```

---

## 6. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-04, UC-05, UC-10 |
| **FR** | FR-REQ-01, FR-REQ-02, FR-REQ-03, FR-REQ-07, FR-REQ-09; FR-NOTIF-01; FR-AUDIT-02 |
| **BR** | BR-06, BR-07, BR-08, BR-18, BR-19, BR-20, BR-22, BR-23, BR-24, BR-26, BR-29 |
| **AC** | AC-APP-01, AC-APP-02, AC-APP-02b, AC-APP-03, AC-APP-08, AC-REQ-07, AC-DRAFT-01, AC-DRAFT-02, AC-NOTIF-01 |
| **RBAC** | создание/edit/submit/cancel — `employee` (инициатор); BR-27 |
| **BPMN** | BPMN-01 |

---

## 7. Границы

- Решения согласующего — UML-SEQ-02.
- Конфигурация admin — UML-SEQ-03.
- HTTP-эндпоинты и разбиение на сервисы **не** моделируются.
- Новые правила не вводятся.
