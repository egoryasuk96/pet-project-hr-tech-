# ADR — JWT для Core API (Stage 5.3)

**Продукт:** Employee Service  
**ID:** ADR-AUTH-JWT-01  
**Версия:** 1.2  
**Статус:** Accepted (Stage 5.3; UI Stage 6.2 Login → My Requests)  
**Связанные документы:** [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [ADR-UI-01](./adr-static-web-client.md), [security-and-crosscutting.md](./security-and-crosscutting.md), [Backlog](../../backlog.md) (UC-01, FR-AUTH-*, NFR-SEC-01/03/04)

---

## Контекст

Ранний Baseline описывал демо-идентификацию через HTTP-заголовок ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md) — **Superseded**). Для Core API и static UI нужен настоящий access token без refresh и без внешнего IdP.

## Решение

1. Для HTTP API используется **JWT access token** (Bearer), а не demo-header.
2. Login: `POST /auth/login` по `login` / `password`; текущий пользователь: `GET /me`.
3. Пароли хранятся только как **bcrypt** hash (`password_hash`). Plaintext запрещён.
4. TTL access token = **8 часов** (NFR-SEC-04). Refresh tokens отсутствуют.
5. Секрет подписи — переменная окружения `JWT_SECRET` (NFR-DEP-03).
6. Demo-header **не** принимается как AuthN. ADR-AUTH-DEMO-01 — только HISTORICAL stub.
7. Demo-seed может выставить `password_hash` из `DEMO_PASSWORD` (только env), без записи пароля в репозиторий.
8. Пользователь и RBAC: JWT `sub` → User; одна системная роль `User.role_id` (`employee` | `approver` | `admin`).

Это **не** новый FR/BR: FR-AUTH-01…03 и NFR-SEC-01/03/04 — Target-active (не backlog).

## Последствия

- Защищённые endpoint'ы требуют валидный JWT; иначе `401 ERR_UNAUTHORIZED`.
- Неверные учётные данные → `401 ERR_INVALID_CREDENTIALS`.
- Авторизация (RBAC + ownership) по-прежнему на backend (BR-01, BR-16, ACL-01).
- Static HTML/JS клиент (ADR-UI-01) использует этот же JWT login, а не Role Select / demo-header.

### Клиентское хранение токена (Stage 6.2)

Способ хранения на клиенте ранее не был зафиксирован. Для многостраничного HTML:

1. После `POST /auth/login` клиент сохраняет в **`sessionStorage`** ключ `employee_service_session`: `access_token`, `token_type`, `expires_in`, `user` (из `LoginResponse`).
2. Защищённые запросы шлют `Authorization: Bearer <access_token>`.
3. Нет токена или ответ `401` → очистить storage и перейти на `/login`.
4. «Выйти» — очистка storage и переход на `/login` (отдельного logout endpoint нет; JWT stateless).
5. Имя в шапке берётся из `user.full_name` ответа login (без обязательного `GET /me` для этого среза).
6. Refresh-token механизм **не** вводится.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-21 | JWT Core API для Stage 5.3 |
| 1.1 | 2026-09-23 | Уточнение: UI опирается на JWT (Stage 6.0 docs sync) |
| 1.2 | 2026-09-23 | sessionStorage для static HTML/JS (Login → My Requests) |
| 1.3 | 2026-09-24 | Context: ADR-DEMO historical; FR-AUTH Target-active |
