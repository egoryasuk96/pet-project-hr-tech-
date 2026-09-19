# UML-SEQ-02 — Sequence: решение на этапе согласования

**Проект:** Employee Service  
**Тип диаграммы:** Sequence  
**Файл индекса:** [uml-description.md](./uml-description.md)  
**Связь с BPMN:** [BPMN-02](../bpmn/to-be-approval-stage.md)

---

## 1. Назначение

Взаимодействия согласующего и системы при approve / reject / return. Зафиксированы:

- **first-approve wins** (BR-03);
- **запрет самосогласования** (BR-21);
- **обязательность комментария** при reject/return (BR-25);
- чтение **route snapshot** без пересоздания.

---

## 2. Участники (lifelines)

| Lifeline | Смысл |
| :--- | :--- |
| **Согласующий A** | Assignee открытой задачи |
| **Согласующий B** | Второй assignee того же этапа (для first-approve) |
| **Инициатор** | Владелец заявки (получатель уведомлений; субъект запрета self-approval) |
| **Система** | Граница Employee Service |

### 2.1. Логические области ответственности (не архитектура)

Имена **Validation**, **Snapshot** (чтение route snapshot), **TaskFactory**, **Audit**, **Notification** — **логические роли / области ответственности на уровне анализа**.

Они **не** микросервисы, **не** компоненты архитектуры и **не** API.

---

## 3. Основные сценарии

### 3.1. Approve (happy path)

1. A открывает задачу → полная карточка заявки (BR-14).
2. Validation: задача открыта и принадлежит A (BR-15); A ≠ инициатор (BR-21).
3. Approve; комментарий необязателен (BR-25).
4. Задача A → completed; прочие **активные** задачи этапа → `cancelled` (BR-03).
5. Snapshot: определить next step **по существующему route snapshot**.
6. Есть следующий этап → TaskFactory создаёт задачи; статус остаётся `in_approval`.
7. Нет следующего → статус `approved` (BR-17).
8. Audit + Notification (BR-29).

### 3.2. Reject

1. Reject + **обязательный** комментарий (BR-25).
2. Статус `rejected`; открытые задачи этапа закрыты (BR-04).
3. Последующие этапы не создаются.
4. Уведомление инициатору.

### 3.3. Return

1. Return + **обязательный** комментарий (BR-25).
2. Статус `returned`; номер этапа сохранён; задачи этапа закрыты (BR-05).
3. Уведомление инициатору; дальнейший resubmit — UML-SEQ-01.

### 3.4. Исключения

| Условие | Результат |
| :--- | :--- |
| Пустой комментарий при reject/return | ERR_VALIDATION; статус без изменений |
| Инициатор пытается решить по своей заявке | ERR_FORBIDDEN_APPROVAL (BR-21) |
| Чужая или неоткрытая задача | ERR_FORBIDDEN_APPROVAL / ERR_TASK_DONE |
| Повторный approve после first-approve (задача B cancelled) | ERR_TASK_DONE / ERR_DUP_ACTION |

---

## 4. Sequence: approve и first-approve wins (Mermaid)

```mermaid
sequenceDiagram
  actor A as Согласующий A
  actor B as Согласующий B
  participant Sys as Система
  actor Init as Инициатор
  Note over Sys: Логические области анализа<br/>(не сервисы/API): Validation, Snapshot,<br/>TaskFactory, Audit, Notification

  A->>Sys: Открыть задачу / карточку заявки
  Sys-->>A: полная карточка (BR-14)

  A->>Sys: Approve (комментарий опционален)
  Sys->>Sys: Validation: своя открытая задача; не инициатор
  alt Self-approval или нет прав
    Sys-->>A: ERR_FORBIDDEN_APPROVAL
  else OK
    Sys->>Sys: задача A = completed
    Sys->>Sys: first-approve: активные задачи этапа → cancelled (BR-03)
    Note over B: задача B cancelled
    Sys->>Sys: Snapshot: next step по route snapshot (только чтение)
    alt Есть следующий этап
      Sys->>Sys: TaskFactory: задачи следующего этапа
      Sys->>Sys: Audit + Notification новым assignees
      Sys-->>A: этап пройден; заявка in_approval
    else Последний этап
      Sys->>Sys: status = approved
      Sys->>Sys: Audit + Notification инициатору
      Sys-->>Init: уведомление approved
      Sys-->>A: маршрут завершён
    end
  end

  B->>Sys: Approve по своей задаче
  Sys-->>B: ERR_TASK_DONE / ERR_DUP_ACTION
```

---

## 5. Sequence: reject / return / self-approval (Mermaid)

```mermaid
sequenceDiagram
  actor Appr as Согласующий
  participant Sys as Система
  actor Init as Инициатор
  Note over Sys: Логические области анализа<br/>(не сервисы/API)

  alt Reject
    Appr->>Sys: Reject + комментарий
    Sys->>Sys: Validation: права; комментарий непустой (BR-25)
    alt Пустой комментарий
      Sys-->>Appr: ERR_VALIDATION
    else OK
      Sys->>Sys: status = rejected; закрыть задачи этапа
      Sys->>Sys: Audit + Notification инициатору
      Sys-->>Init: уведомление rejected
      Sys-->>Appr: заявка rejected
    end
  else Return
    Appr->>Sys: Return + комментарий
    Sys->>Sys: Validation: права; комментарий непустой (BR-25)
    alt Пустой комментарий
      Sys-->>Appr: ERR_VALIDATION
    else OK
      Sys->>Sys: status = returned; сохранить этап N; закрыть задачи
      Sys->>Sys: Audit + Notification инициатору
      Sys-->>Init: уведомление returned
      Sys-->>Appr: заявка returned
    end
  else Самосогласование
    Init->>Sys: Approve/Reject/Return по своей заявке
    Sys->>Sys: Validation: actor == инициатор
    Sys-->>Init: ERR_FORBIDDEN_APPROVAL (BR-21)
  end
```

---

## 6. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-07, UC-08, UC-09 |
| **FR** | FR-APP-01…07; FR-REQ-08; FR-NOTIF-01; FR-AUDIT-02 |
| **BR** | BR-02, BR-03, BR-04, BR-05, BR-14, BR-15, BR-17, BR-21, BR-25, BR-29 |
| **AC** | AC-APP-04, AC-APP-04b, AC-APP-05, AC-APP-05b, AC-APP-06, AC-APP-06b, AC-APP-07, AC-APP-07b, AC-APP-09, AC-ACC-02, AC-ACC-03, AC-ACC-06 |
| **RBAC/ACL** | ACL-02, ACL-03, ACL-07 |
| **BPMN** | BPMN-02 |

---

## 7. Границы

- Create / submit / resubmit / cancel — UML-SEQ-01.
- Route snapshot в этом сценарии **только читается**.
- HTTP / микросервисы **не** моделируются.
- Новые правила не вводятся.
