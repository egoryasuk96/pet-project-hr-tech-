# ADR — Лёгкий веб-клиент: статические HTML + JavaScript

**Продукт:** Employee Service  
**ID:** ADR-UI-01  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [Vision & Scope](../../01-vision-and-scope/vision-scope.md) §12 п.7–8, [Backlog](../../backlog.md)

---

## Контекст

Ранее в ранних версиях архитектуры предполагался отдельный **React + TypeScript SPA** как deployable Web-контейнер с login UI и хранением JWT на клиенте (ADR-CNT-03, ADR-SEC-02, ADR-CMP-02 в части SPA). Vision §12 зафиксировал иной контур для Baseline MVP: портфолио-демо без React/SPA и без настоящей аутентификации.

Нужно явно заменить UI-стек Baseline, сохранив историю прежних ADR как **Superseded**.

---

## Решение

1. Решение «React + TypeScript SPA как отдельный Web-контейнер» **superseded** для Baseline.
2. Baseline UI = **статические HTML-страницы + JavaScript**, которые **отдаёт тот же FastAPI**-приложение (один deployable-процесс: REST API + раздача статики / static mount). Отдельный React-контейнер **не** используется.
3. Пять экранов Vision: выбор роли, мои заявки, создание заявки, карточка заявки, очередь согласующего.
4. Идентичность в MVP — демо-роль через заголовок ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)); login/JWT UI — [backlog](../../backlog.md).
5. Admin UI, уведомления, профиль — вне Baseline UI (Vision §12 п.9; backlog).

Источники: Vision §12 п.7–8.

---

## Последствия

| + | − |
| :--- | :--- |
| Согласованность с Vision и минимальный стек портфолио | Нет богатого SPA-роутинга / component tree React |
| Один процесс FastAPI упрощает Compose/демо | Полный JWT/login UI возвращается только из backlog |
| Пять экранов ядра проверяемы без отдельного FE build | ADR-CNT-03 / ADR-SEC-02 / SPA-часть ADR-CMP-02 помечены Superseded |

---

## Что возвращается в полной версии

Из [docs/backlog.md](../../backlog.md) и прежних ADR:

- экран login (UC-01), JWT на клиенте (бывшие ADR-CNT-03 / ADR-SEC-02);
- middleware JWT (бывший ADR-SEC-03) вместо демо-заголовка;
- при необходимости — более развитый клиент (не обязательно React; решение отдельно).

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Baseline UI: static HTML+JS от FastAPI; React SPA superseded |
