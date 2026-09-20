# UML-UC-01 — Use Case Overview

**Продукт:** Employee Service  
**ID:** UML-UC-01  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [uml-description.md](./uml-description.md), [Use Cases](../../02-requirements/use-cases.md)

---

## 1. Назначение

Обзор границ системы Employee Service и связей актёров с пользовательскими сценариями UC-01…UC-15. Диаграмма задаёт контекст для sequence / state / class моделей UML и дополняет BPMN (где процессы login/catalog/просмотр не выносились отдельно).

Новые use case и бизнес-правила **не вводятся**.

---

## 2. Актёры

| Актёр | Код роли | Описание |
| :--- | :--- | :--- |
| **Сотрудник (Инициатор)** | `employee` | Создаёт и ведёт свои заявки; каталог; профиль — Future / backlog |
| **Согласующий** | `approver` | Очередь задач; approve / reject / return |
| **Администратор** | `admin` | Типы, поля, маршрут, назначения, справочники; реестр — Future / backlog |
| **Аутентифицированный пользователь** | — | Обобщение для входа и уведомлений (Future / backlog); конкретные роли — specialization |

Один пользователь может иметь несколько ролей одновременно (BR-16, union permissions). Выбор «активной роли» не требуется.

---

## 3. Пакеты сценариев

| Пакет | UC | Кратко |
| :--- | :--- | :--- |
| Auth & кабинет | UC-01, UC-02, UC-13 | Login, профиль, in-app уведомления — Future / backlog |
| Каталог и заявки | UC-03, UC-04, UC-05, UC-06, UC-10 | Каталог, draft, submit, просмотр, отмена |
| Согласование | UC-07, UC-08, UC-09 | Approve / reject / return |
| Администрирование | UC-11, UC-12, UC-15 | Тип/поля/маршрут; реестр — Future / backlog |
| История | UC-14 | Хронология по заявке (в рамках прав) |

---

## 4. Матрица актёров × UC

| UC | Название | Employee | Approver | Admin | Auth user |
| :--- | :--- | :---: | :---: | :---: | :---: |
| UC-01 | Login | — | — | — | Primary (**Future / backlog**) |
| UC-02 | View Profile | **Future / backlog** | — | — | (свои данные) |
| UC-03 | Browse Service Catalog | Primary | — | — | — |
| UC-04 | Create Request | Primary | — | — | — |
| UC-05 | Submit Request | Primary | — | — | — |
| UC-06 | View My Request | Primary | — | — | — |
| UC-07 | Approve Request | — | Primary | — | — |
| UC-08 | Reject Request | — | Primary | — | — |
| UC-09 | Return Request | — | Primary | — | — |
| UC-10 | Cancel Request | Primary | — | — | — |
| UC-11 | Configure Request Type | — | — | Primary (**Future / backlog**) | — |
| UC-12 | Configure Approval Route | — | — | Primary (**Future / backlog**) | — |
| UC-13 | View Notifications | — | — | — | Primary (**Future / backlog**) |
| UC-14 | View Request History | Primary* | Primary* | **Future / backlog** | — |
| UC-15 | Admin View Requests | — | — | Primary (**Future / backlog**) | — |

\* Baseline в рамках прав видимости: employee — свои заявки, approver — заявки по своей задаче (BR-01, BR-14). Просмотр admin истории любой заявки — **Future / backlog** (BR-13, FR-ADMIN-08).

---

## 5. Диаграмма (Mermaid)

```mermaid
flowchart LR
  subgraph System["Employee Service"]
    UC_01[UC-01 Login]
    UC_02[UC-02 View Profile]
    UC_03[UC-03 Catalog]
    UC_04[UC-04 Create Request]
    UC_05[UC-05 Submit Request]
    UC_06[UC-06 View My Request]
    UC_07[UC-07 Approve]
    UC_08[UC-08 Reject]
    UC_09[UC-09 Return]
    UC_10[UC-10 Cancel]
    UC_11[UC-11 Configure Type]
    UC_12[UC-12 Configure Route]
    UC_13[UC-13 Notifications]
    UC_14[UC-14 History]
    UC_15[UC-15 Admin Registry]
  end

  AuthUser[Аутентифицированный пользователь]
  Employee[Сотрудник employee]
  Approver[Согласующий approver]
  Admin[Администратор admin]

  AuthUser -.->|Future / backlog| UC_01
  AuthUser -.->|Future / backlog| UC_13
  Employee -.->|Future / backlog| UC_02
  Employee --> UC_03
  Employee --> UC_04
  Employee --> UC_05
  Employee --> UC_06
  Employee --> UC_10
  Employee --> UC_14
  Approver --> UC_07
  Approver --> UC_08
  Approver --> UC_09
  Approver --> UC_14
  Admin -.->|Future / backlog| UC_11
  Admin -.->|Future / backlog| UC_12
  Admin -.->|Future / backlog| UC_15
  Admin -.->|Future / backlog| UC_14

  UC_05 -.->|include: валидация схемы и маршрута| UC_04
  UC_08 -.->|constraint: комментарий обязателен BR-25| NoteReject[BR-25]
  UC_09 -.->|constraint: комментарий обязателен BR-25| NoteReturn[BR-25]
  UC_07 -.->|constraint: не инициатор BR-21; first-approve BR-03| NoteApr[BR-21 BR-03]
  UC_05 -.->|snapshot маршрута BR-08 / BR-22| NoteSnap[BR-08 BR-22]
```

Примечания к связям:

- `include` показан упрощённо: submit опирается на созданную/заполненную заявку (UC-04) и проверки BR-18 / BR-26.
- Constraints на UC-07…09 и UC-05 — **существующие** BR, не новые use case.

---

## 6. Аннотации ключевых правил на UC

| UC | Правило | Смысл |
| :--- | :--- | :--- |
| UC-05 | BR-08, BR-22, BR-26 | Первый submit → route snapshot; каждый submit → schema/value snapshot; resubmit не трогает route |
| UC-07 | BR-03, BR-21, BR-25 | First-approve wins; запрет самосогласования; комментарий при approve необязателен |
| UC-08, UC-09 | BR-21, BR-25 | Запрет самосогласования; комментарий обязателен |
| UC-10 | BR-07 | Отмена только `draft` / `returned` |
| UC-11, UC-12 | BR-09, BR-18, BR-27 | Изоляция snapshot; валидация маршрута при активации; admin не создаёт заявки от сотрудника |

---

## 7. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-01…UC-15 |
| **FR** | FR-AUTH-*, FR-CAB-*, FR-CAT-*, FR-REQ-*, FR-APP-*, FR-NOTIF-*, FR-AUDIT-*, FR-ADMIN-* (обзорно) |
| **BR** | BR-01, BR-03, BR-07, BR-08, BR-09, BR-13–16, BR-21, BR-22, BR-25, BR-26, BR-27 |
| **AC** | AC-AUTH-01, AC-ACC-*, AC-CAT-*, AC-APP-* (обзорно через связанные UC) |
| **RBAC** | матрица ролей; ACL-01…03, ACL-05…08; ACL-04, ACL-09 — Future / backlog |

---

## 8. Границы

- Детали взаимодействий — UML-SEQ-01…03.
- Статусы заявки — UML-SM-01.
- Структура предметной области — UML-CL-01.
- Процессные потоки — BPMN-01…03.
- Новые правила не вводятся.
