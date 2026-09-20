# Матрица ошибок

**Продукт:** Employee Service  
**Документ:** Error Matrix  
**ID:** DOC-ERR  
**Версия:** 1.0  
**Статус:** Baseline v1.0

Документ задаёт коды ошибок для будущего REST API. **Конкретные endpoint на этом этапе не проектируются.**

Рекомендуемый формат тела ошибки (ориентир для будущего контракта API / OpenAPI):

```json
{
  "error_code": "ERR_FORBIDDEN",
  "message": "Недостаточно прав для выполнения операции",
  "details": {}
}
```

---

## 1. Матрица (ядро Baseline)

| Error code | HTTP status | Condition | User message | System behavior |
| :--- | :---: | :--- | :--- | :--- |
| ERR_FORBIDDEN | 403 | Роль не позволяет операцию | Недостаточно прав для выполнения операции | Состояние данных не меняется |
| ERR_FORBIDDEN_APPROVAL | 403 | Пользователь не assignee задачи, либо самосогласование (BR-15, BR-21) | Вы не можете выполнить действие по этой задаче | Заявка и задача не меняются |
| ERR_NOT_FOUND | 404 | Ресурс не существует **или** скрыт правилами видимости (чужая заявка) | Объект не найден | Состояние не меняется |
| ERR_VALIDATION | 422 | Нарушение схемы/обязательных полей/форматов/page_size | Проверьте корректность заполнения полей | Детали по полям в `details`; запись не создаётся/не обновляется |
| ERR_INACTIVE_TYPE | 409 | Попытка создать/отправить заявку по неактивному типу (BR-10) | Этот тип заявки недоступен | Заявка не создаётся / submit не выполняется |
| ERR_INVALID_STATE | 409 | Действие недопустимо в текущем статусе заявки/задачи (cancel не из draft/returned, edit не из draft/returned, submit не из draft/returned и т.п.) | Действие недоступно для текущего статуса | Статус не меняется; пишется технический лог |
| ERR_TASK_DONE | 409 | Задача уже завершена (approve/reject/return уже выполнены или закрыта системой) | Задача уже обработана | Повторное решение не применяется |
| ERR_DUP_ACTION | 409 | Повтор того же бизнес-действия в условиях гонки/повтора запроса | Действие уже было выполнено | Идемпотентный отказ; итоговое состояние сохраняется |
| ERR_ROUTE_CONFIG | 409 | Маршрут типа невалиден при submit (и при активации типа — admin backlog): нет этапов и/или нет назначений (BR-18) | Маршрут согласования настроен некорректно | Submit отклоняется; draft/returned сохраняется |
| ERR_CONFLICT_VERSION | — | **Не используется в MVP.** Optimistic locking не реализуется | — | — |
| ERR_INTERNAL | 500 | Непредвиденная ошибка сервера | Произошла внутренняя ошибка. Попробуйте позже | Rollback транзакции; ошибка в технический лог с request_id; клиенту без stack trace |

---

## 1b. Backlog auth errors (отложено вместе с login/JWT)

Коды `ERR_INVALID_CREDENTIALS` и `ERR_UNAUTHORIZED` остаются в словаре API; сценарии login/JWT отложены. Отложенные функции и ACL admin/login — см. [backlog.md](../backlog.md).

---

## 2. Минимальное покрытие (чеклист)

| Требование заказчика | Error code | Baseline / backlog |
| :--- | :--- | :--- |
| invalid credentials | ERR_INVALID_CREDENTIALS | backlog (auth) |
| unauthorized | ERR_UNAUTHORIZED | backlog (auth) |
| forbidden | ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL | Baseline |
| resource not found | ERR_NOT_FOUND | Baseline |
| validation error | ERR_VALIDATION | Baseline |
| inactive request type | ERR_INACTIVE_TYPE | Baseline |
| invalid request state | ERR_INVALID_STATE | Baseline |
| user cannot perform approval | ERR_FORBIDDEN_APPROVAL | Baseline |
| task already completed | ERR_TASK_DONE | Baseline |
| route configuration error | ERR_ROUTE_CONFIG | Baseline (submit); активация типа — backlog admin |
| duplicate action | ERR_DUP_ACTION | Baseline |
| internal error | ERR_INTERNAL | Baseline |

---

## 3. Связь с BR / FR (Baseline)

| Error code | BR / FR |
| :--- | :--- |
| ERR_INACTIVE_TYPE | BR-10, FR-CAT-01, FR-REQ-01 |
| ERR_INVALID_STATE | BR-07, BR-19, BR-20, FR-REQ-07 |
| ERR_FORBIDDEN_APPROVAL | BR-15, BR-21, FR-APP-03–05 |
| ERR_TASK_DONE | BR-03, NFR-REL-02 |
| ERR_ROUTE_CONFIG | BR-18, FR-REQ-03 |
| ERR_NOT_FOUND | BR-01, BR-14, NFR-SEC-05 |
| ERR_VALIDATION | BR-25, BR-26, FR-REQ-02, FR-APP-04, FR-APP-05 |

---

## 4. Open Questions / TBD

**Обязательных открытых вопросов по error-matrix для Baseline нет.**

Примечание: пустой каталог **не является ошибкой** и в матрицу ошибок не входит.

---

## 5. Трассировка

Ошибки ядра используются в AC негативных сценариев Baseline: AC-ACC-01…03, AC-ACC-06, AC-CAT-01, AC-APP-*, AC-REQ-07.  
Детальная привязка к path/method — после Baseline (OpenAPI).
