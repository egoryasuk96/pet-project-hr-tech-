# ADR — JWT для Core API (Stage 5.3)

**Продукт:** Employee Service  
**ID:** ADR-AUTH-JWT-01  
**Версия:** 1.0  
**Статус:** Accepted (Stage 5.3)  
**Связанные документы:** [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [security-and-crosscutting.md](./security-and-crosscutting.md), [Backlog](../../backlog.md) (UC-01, FR-AUTH-*, NFR-SEC-01/03/04)

---

## Контекст

Baseline MVP описывает демо-идентификацию через HTTP-заголовок ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)). Login/password и JWT вынесены в backlog.

Stage 5.3 реализует вертикальный сценарий сотрудника, включая аутентификацию. Для Core API нужен настоящий access token без refresh и без внешнего IdP.

## Решение

1. Для HTTP API Stage 5.3 используется **JWT access token** (Bearer), а не demo-header.
2. Login: `POST /auth/login` по `login` / `password`; текущий пользователь: `GET /me`.
3. Пароли хранятся только как **bcrypt** hash (`password_hash`). Plaintext запрещён.
4. TTL access token = **8 часов** (NFR-SEC-04). Refresh tokens отсутствуют.
5. Секрет подписи — переменная окружения `JWT_SECRET` (NFR-DEP-03).
6. Demo-header **не** принимается как AuthN. ADR-AUTH-DEMO-01 остаётся описанием Baseline-stub до UI; runtime Core API ему не следует.
7. Demo-seed может выставить `password_hash` из `DEMO_PASSWORD` (только env), без записи пароля в репозиторий.

Это **не** новый FR/BR: используются уже зафиксированные backlog FR-AUTH-01…03 и NFR-SEC-01/03/04, выведенные в реализацию раньше UI.

## Последствия

- Защищённые endpoint'ы требуют валидный JWT; иначе `401 ERR_UNAUTHORIZED`.
- Неверные учётные данные → `401 ERR_INVALID_CREDENTIALS`.
- Авторизация (RBAC + ownership) по-прежнему на backend (BR-01, BR-16, ACL-01).

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-21 | JWT Core API для Stage 5.3 |
