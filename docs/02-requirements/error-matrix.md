# Матрица ошибок

**Продукт:** Employee Service  
**Документ:** Error Matrix  
**ID:** DOC-ERR  
**Версия:** 1.3  
**Статус:** Target architecture (runtime E3.2.1)  
**Связанные документы:** [ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md)

Документ задаёт коды ошибок REST API.

**Целевой формат тела** ([ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md) — **нормативен для Target**):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Недостаточно прав для выполнения операции",
    "details": {}
  }
}
```

Legacy runtime (до смены кода) мог отдавать плоский `{ "error_code", "message", "details" }` с префиксом `ERR_`. Ниже — **канон Target** плюс соответствие старым кодам. Runtime E3.2.1 использует только nested envelope и канонические `error.code`.

---

## 1. Матрица (ядро)

| Error code (target) | Legacy | HTTP | Condition | User message | System behavior |
| :--- | :--- | :---: | :--- | :--- | :--- |
| FORBIDDEN | ERR_FORBIDDEN | 403 | Роль не позволяет операцию | Недостаточно прав для выполнения операции | Состояние данных не меняется |
| FORBIDDEN_APPROVAL | ERR_FORBIDDEN_APPROVAL | 403 | Не assignee / самосогласование (BR-15, BR-21) | Вы не можете выполнить действие по этой задаче | Заявка и задача не меняются |
| NOT_FOUND | ERR_NOT_FOUND | 404 | Ресурс не существует или скрыт ACL | Объект не найден | Состояние не меняется |
| VALIDATION | ERR_VALIDATION | 422 | Схема / поля / page_size | Проверьте корректность заполнения полей | `details`; запись не создаётся |
| INACTIVE_TYPE | ERR_INACTIVE_TYPE | 409 | Неактивный тип заявки (BR-10) | Этот тип заявки недоступен | Create/submit не выполняется |
| INVALID_STATE / REQUEST_ACTION_NOT_ALLOWED | ERR_INVALID_STATE | 409 | Действие недопустимо / transition не подходит | Действие недоступно для текущего статуса | Статус не меняется |
| TASK_DONE | ERR_TASK_DONE | 409 | Задача уже завершена | Задача уже обработана | Повтор не применяется |
| DUP_ACTION | ERR_DUP_ACTION | 409 | Повтор действия / гонка | Действие уже было выполнено | Идемпотентный отказ |
| ROUTE_CONFIG | ERR_ROUTE_CONFIG | 409 | Невалидный live-маршрут при submit (BR-18) | Маршрут согласования настроен некорректно | Submit отклонён |
| INVALID_CREDENTIALS | ERR_INVALID_CREDENTIALS | 401 | Неверный логин/пароль | Неверный логин или пароль | Токен не выдаётся |
| UNAUTHORIZED | ERR_UNAUTHORIZED | 401 | Нет/битый JWT | Требуется аутентификация | — |
| PASSWORD_MISMATCH | — | 409 | Неверный текущий пароль при смене | Текущий пароль неверен | Hash не меняется |
| INTERNAL | ERR_INTERNAL | 500 | Непредвиденная ошибка | Произошла внутренняя ошибка. Попробуйте позже | Rollback; без stack trace клиенту |

Frontend показывает пользователю только `error.message`.

---

## 2. Минимальное покрытие (чеклист)

| Требование | Error code |
| :--- | :--- |
| invalid credentials | INVALID_CREDENTIALS |
| unauthorized | UNAUTHORIZED |
| forbidden | FORBIDDEN / FORBIDDEN_APPROVAL |
| not found | NOT_FOUND |
| validation | VALIDATION |
| inactive type | INACTIVE_TYPE |
| invalid state / action | INVALID_STATE / REQUEST_ACTION_NOT_ALLOWED |
| task done | TASK_DONE |
| route config | ROUTE_CONFIG |
| duplicate action | DUP_ACTION |
| password mismatch | PASSWORD_MISMATCH |
| internal | INTERNAL |

---

## 3. Связь с BR / FR

| Error code | BR / FR |
| :--- | :--- |
| INACTIVE_TYPE | BR-10, FR-CAT-01, FR-REQ-01 |
| INVALID_STATE / REQUEST_ACTION_NOT_ALLOWED | BR-07, BR-19, BR-20, FR-REQ-07; ADR-ACTION-01 |
| FORBIDDEN_APPROVAL | BR-15, BR-21, FR-APP-03–05 |
| TASK_DONE | BR-03, NFR-REL-02 |
| ROUTE_CONFIG | BR-18, FR-REQ-03 |
| NOT_FOUND | BR-01, BR-14, NFR-SEC-05 |
| VALIDATION | BR-25, BR-26, FR-REQ-02 |

---

## 4. Action Engine (`POST /requests/{id}/actions/{action_id}`)

Единый execute endpoint использует только канонические коды из §1. HTTP:

| Ситуация | `error.code` | HTTP |
| :--- | :--- | :---: |
| Нет заявки / нет action / чужая заявка для employee | `NOT_FOUND` | 404 |
| Transition не найден / роль или статус не допускают действие / неконсистентное состояние | `REQUEST_ACTION_NOT_ALLOWED` | 409 |
| Self-approval (BR-21) / нет open ApprovalTask текущего пользователя (BR-15) | `FORBIDDEN_APPROVAL` | 403 |
| Пустой обязательный comment (reject/return, BR-25) | `VALIDATION` | 422 |
| Невалидный live-маршрут при создании задач (BR-18) | `ROUTE_CONFIG` | 409 |

Кратковременные коды E3.2 (`REQUEST_NOT_FOUND`, `ACTION_NOT_ALLOWED`, …) сняты в E3.2.1 в пользу таблицы выше.

---

## 5. Open Questions / TBD

Нет открытых вопросов по Target error contract после E3.2.1.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Baseline плоский ERR_* |
| 1.1 | 2026-09-23 | Target nested envelope; legacy flat ERR_* mapping |
| 1.2 | 2026-09-23 | Ссылка на ADR-ERR-03 (устранена коллизия с ADR-ERR-02 TX) |
| 1.3 | 2026-09-23 | E3.2.1: Action Engine → канонические коды (§4) |
