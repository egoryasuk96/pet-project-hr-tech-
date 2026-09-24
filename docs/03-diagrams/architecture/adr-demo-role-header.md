# ADR — Демо-идентификация: роль через заголовок

**Продукт:** Employee Service  
**ID:** ADR-AUTH-DEMO-01  
**Версия:** 1.1  
**Статус:** **Superseded** → [ADR-AUTH-JWT-01](./adr-jwt-core-api.md)  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [Vision & Scope](../../01-vision-and-scope/vision-scope.md)

---

## Статус

**HISTORICAL / Superseded.** Документ сохранён как описание раннего Baseline-stub. Для CURRENT/TARGET runtime **не** применяется: AuthN = JWT Bearer ([ADR-AUTH-JWT-01](./adr-jwt-core-api.md)).

---

## Контекст (исторический)

Employee Service — портфолио-демо ядра workflow заявок. На раннем Baseline настоящая аутентификация (login/password, JWT) ещё не была в runtime; нужен был простой способ переключать актёра (`employee` / `approver` / при необходимости `admin` в seed) для ручной проверки сценариев.

---

## Решение (исторический stub)

1. Настоящий AuthN **отсутствовал** в раннем Baseline.
2. Демо-роль (и при необходимости идентификатор пользователя) передавалась **HTTP-заголовком** с клиента на API.
3. Экран **выбора роли** — точка входа демо: пользователь выбирал роль/демо-пользователя; клиент запоминал выбор и подставлял заголовок.
4. Проверки доступа опирались на значение заголовка + seed RBAC (ownership, задачи), без JWT.

Это был **технический stub**, не новый UC/FR ID.

---

## Последствия (на момент Baseline)

| + | − |
| :--- | :--- |
| Быстрый демо-контур без login UI | Заголовок подделывался клиентом — только для локального/демо стенда |
| Экраны ядра проверялись без JWT | NFR/SEC про JWT не применялись к тому runtime |
| Ясный путь к полной auth | Документы должны явно отличать stub от целевой модели |

---

## Замена (CURRENT / TARGET)

- [ADR-AUTH-JWT-01](./adr-jwt-core-api.md): `POST /auth/login` → JWT access token; `Authorization: Bearer`; RBAC через `User.role_id`.
- Demo-header **не** принимается как AuthN.
- Refresh tokens не используются.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Зафиксирован stub: роль в заголовке + экран выбора роли |
| 1.1 | 2026-09-24 | Status → Superseded by ADR-AUTH-JWT-01; текст — HISTORICAL |
