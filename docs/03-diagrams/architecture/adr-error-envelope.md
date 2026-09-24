# ADR — Единый формат ошибок API (envelope)

**Продукт:** Employee Service  
**ID:** ADR-ERR-03  
**Версия:** 1.1  
**Статус:** Accepted (Target API contract)  
**Связанные документы:** [error-matrix.md](../../02-requirements/error-matrix.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md)

> **Не путать** с ADR-ERR-01 / ADR-ERR-02 в [security-and-crosscutting.md](./security-and-crosscutting.md) (маппинг HTTP и validation-before-TX).

---

## Контекст

Baseline / Pre-E2 runtime использовал плоский envelope `{ "error_code", "message", "details" }`. Для Target UI нужен единый machine-readable `code` и human-readable `message`.

---

## Решение (Target — нормативно)

```json
{
  "error": {
    "code": "REQUEST_ACTION_NOT_ALLOWED",
    "message": "Действие «Согласовать» недоступно для заявки в текущем статусе",
    "details": {}
  }
}
```

| Поле | Назначение |
| :--- | :--- |
| `error.code` | Machine-readable код (без префикса `ERR_`) |
| `error.message` | Текст для UI |
| `error.details` | Опциональные детали (напр. validation fields) |

Клиент показывает пользователю **только** `error.message`.

| HTTP | Примеры `error.code` |
| :--- | :--- |
| 401 | `INVALID_CREDENTIALS`, `UNAUTHORIZED` |
| 403 | `FORBIDDEN`, `FORBIDDEN_APPROVAL` |
| 404 | `NOT_FOUND` |
| 409 | `REQUEST_ACTION_NOT_ALLOWED`, `INVALID_STATE`, `TASK_DONE`, `INACTIVE_TYPE`, `ROUTE_CONFIG`, `PASSWORD_MISMATCH` |
| 422 | `VALIDATION` |
| 500 | `INTERNAL` |

**Legacy / Pre-E2 (до смены runtime):** плоский `{ "error_code": "ERR_…", "message", "details" }` — не Target.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-23 | Вложенный envelope (временно как ADR-ERR-02 — коллизия ID) |
| 1.1 | 2026-09-23 | ID переименован в **ADR-ERR-03**; Target нормативен |
