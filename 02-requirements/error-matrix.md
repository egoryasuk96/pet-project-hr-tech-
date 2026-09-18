# Матрица ошибок

**Проект:** Employee Service  
**Документ:** Error Matrix  
**Версия:** 1.0  
**Статус:** Draft (Этап 2)

Документ задаёт коды ошибок для будущего REST API. **Конкретные endpoint на этом этапе не проектируются.**

Рекомендуемый формат тела ошибки (ориентир для Этапа 4):

```json
{
  "error_code": "ERR_FORBIDDEN",
  "message": "Недостаточно прав для выполнения операции",
  "details": {}
}
```

---

## 1. Матрица

| Error code | HTTP status | Condition | User message | System behavior |
| :--- | :---: | :--- | :--- | :--- |
| ERR_INVALID_CREDENTIALS | 401 | Неверный логин и/или пароль | Неверный логин или пароль | Токен не выдаётся; факт существования логина не уточняется |
| ERR_UNAUTHORIZED | 401 | Нет токена, токен просрочен или повреждён | Требуется аутентификация | Запрос отклоняется до бизнес-логики |
| ERR_FORBIDDEN | 403 | Роль не позволяет операцию (например, доступ в админку) | Недостаточно прав для выполнения операции | Состояние данных не меняется |
| ERR_FORBIDDEN_APPROVAL | 403 | Пользователь не assignee задачи, либо самосогласование (BR-15, BR-21) | Вы не можете выполнить действие по этой задаче | Заявка и задача не меняются |
| ERR_NOT_FOUND | 404 | Ресурс не существует **или** скрыт правилами видимости (чужая заявка) | Объект не найден | Состояние не меняется |
| ERR_VALIDATION | 422 | Нарушение схемы/обязательных полей/форматов/page_size | Проверьте корректность заполнения полей | Детали по полям в `details`; запись не создаётся/не обновляется |
| ERR_INACTIVE_TYPE | 409 | Попытка создать/отправить заявку по неактивному типу (BR-10) | Этот тип заявки недоступен | Заявка не создаётся / submit не выполняется |
| ERR_INVALID_STATE | 409 | Действие недопустимо в текущем статусе заявки/задачи (cancel не из draft/returned, edit не из draft/returned, submit не из draft/returned и т.п.) | Действие недоступно для текущего статуса | Статус не меняется; пишется технический лог |
| ERR_TASK_DONE | 409 | Задача уже завершена (approve/reject/return уже выполнены или закрыта системой) | Задача уже обработана | Повторное решение не применяется |
| ERR_DUP_ACTION | 409 | Повтор того же бизнес-действия в условиях гонки/повтора запроса | Действие уже было выполнено | Идемпотентный отказ; итоговое состояние сохраняется |
| ERR_ROUTE_CONFIG | 409 | Маршрут типа невалиден при активации типа или при submit: нет этапов и/или нет назначений (BR-18) | Маршрут согласования настроен некорректно. Обратитесь к администратору / исправьте конфигурацию | Активация типа или submit отклоняется; draft/returned при submit сохраняется |
| ERR_CONFLICT_VERSION | — | **Не используется в MVP.** Optimistic locking в административной части не реализуется | — | — |
| ERR_INTERNAL | 500 | Непредвиденная ошибка сервера | Произошла внутренняя ошибка. Попробуйте позже | Rollback транзакции; ошибка в технический лог с request_id; клиенту без stack trace |

---

## 2. Минимальное покрытие (чеклист)

| Требование заказчика | Error code |
| :--- | :--- |
| invalid credentials | ERR_INVALID_CREDENTIALS |
| unauthorized | ERR_UNAUTHORIZED |
| forbidden | ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL |
| resource not found | ERR_NOT_FOUND |
| validation error | ERR_VALIDATION |
| inactive request type | ERR_INACTIVE_TYPE |
| invalid request state | ERR_INVALID_STATE |
| user cannot perform approval | ERR_FORBIDDEN_APPROVAL |
| task already completed | ERR_TASK_DONE |
| route configuration error | ERR_ROUTE_CONFIG |
| duplicate action | ERR_DUP_ACTION |
| internal error | ERR_INTERNAL |

---

## 3. Связь с BR / FR

| Error code | BR / FR |
| :--- | :--- |
| ERR_INACTIVE_TYPE | BR-10, FR-CAT-01, FR-REQ-01 |
| ERR_INVALID_STATE | BR-07, BR-19, BR-20, FR-REQ-07 |
| ERR_FORBIDDEN_APPROVAL | BR-15, BR-21, FR-APP-03–05 |
| ERR_TASK_DONE | BR-03, NFR-REL-02 |
| ERR_ROUTE_CONFIG | BR-18, FR-REQ-03, FR-ADMIN-01 |
| ERR_NOT_FOUND | BR-01, BR-14, NFR-SEC-05 |
| ERR_VALIDATION | BR-25, BR-26, FR-REQ-02, FR-APP-04, FR-APP-05 |

---

## 4. Open Questions

| ID | Вопрос | Предложение |
| :--- | :--- | :--- |
| OQ-ERR-03 | Код для пустого каталога | Не ошибка: пустой список 200 |

Закрыты: OQ-ERR-01 (404), OQ-ERR-02 (optimistic locking не реализуется) — см. NFR-SEC-05 и ERR_CONFLICT_VERSION out of MVP.

---

## 5. Трассировка

Ошибки используются в AC негативных сценариев: AC-ACC-*, AC-CAT-01, AC-APP-*, AC-REQ-07.  
Детальная привязка к path/method — на Этапе 4 (OpenAPI).
