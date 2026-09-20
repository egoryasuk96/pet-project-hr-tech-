# Архитектура Employee Service (логико-техническая модель)

**Продукт:** Employee Service  
**ID:** ARCH-00  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [BPMN](../bpmn/bpmn-description.md), [UML](../uml/uml-description.md), [Snapshot Model](../erd/snapshot-model.md), [ADR snapshot](./adr-snapshot-submit-versions.md), [ADR demo role](./adr-demo-role-header.md), [Vision](../../01-vision-and-scope/vision-scope.md)

---

## 1. Назначение

Документ фиксирует **логическую и техническую архитектуру** MVP Employee Service на уровне системного аналитика: границы системы, контейнеры (веб-клиент / backend / database), логические компоненты, потоки данных, зоны ответственности, место ключевых бизнес-правил, безопасность, ошибки, аудит, ограничения масштабируемости и производительности.

Новые бизнес-правила **не вводятся** этим индексом. Архитектура **реализует** процессы (BPMN) и аналитические взаимодействия (UML), не заменяя их.

---

## 2. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; визуал — Mermaid |
| **Язык** | Русский |
| **Трассировка** | Ссылки на UC / FR / BR / AC / NFR / RBAC |
| **Требование vs ADR** | Зафиксированное в Stage 1–3.2 — требование; иное — **ADR / предположение MVP** |
| **Логические модули** | Разбиение монолита, не микросервисы |
| **Snapshot** | Полная механика только в [Snapshot Model](../erd/snapshot-model.md) |

### 2.1. ADR

| Метка | Смысл |
| :--- | :--- |
| **Требование** | Vision / FR / BR / NFR / AC / RBAC / BPMN / UML |
| **ADR (MVP)** | Архитектурное решение; **не** новый FR/BR/NFR |

Отдельные ADR Baseline:

- [ADR-SNAP-01](./adr-snapshot-submit-versions.md) — вариант B: RouteInstance + FieldValueVersion;
- [ADR-AUTH-DEMO-01](./adr-demo-role-header.md) — демо-роль через заголовок + экран выбора роли.

Прочие ADR (модули, TX) — в файлах этапа.

---

## 3. Архитектурный стиль (ADR)

**Выбор:** модульный монолит — один backend + лёгкий веб-клиент (HTML/JS) + одна БД.

**Обоснование:** один bounded context; атомарность status + tasks + history; объём MVP; стек PostgreSQL + FastAPI + статика.

---

## 4. Список артефактов

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ARCH-00 | [architecture-description.md](./architecture-description.md) | Индекс, соглашения, DoD |
| ARCH-CTX | [context-diagram.md](./context-diagram.md) | Граница системы и актёры |
| ARCH-CNT | [container-diagram.md](./container-diagram.md) | Web / API / DB |
| ARCH-CMP | [component-diagram.md](./component-diagram.md) | Логические модули и UI-зоны |
| ARCH-FLOW | [data-flows.md](./data-flows.md) | Потоки submit / approval / admin |
| ARCH-SEC | [security-and-crosscutting.md](./security-and-crosscutting.md) | Auth stub, ошибки, логи, NFR |
| ARCH-MAP | [architecture-traceability.md](./architecture-traceability.md) | Трассировка |
| ADR-SNAP-01 | [adr-snapshot-submit-versions.md](./adr-snapshot-submit-versions.md) | Вариант B |
| ADR-AUTH-DEMO-01 | [adr-demo-role-header.md](./adr-demo-role-header.md) | Роль в заголовке |

---

## 5. Сводка: критичные правила → владелец

| Правило | Источник | Владелец |
| :--- | :--- | :--- |
| RouteInstance только при первом submit | BR-08, BR-22; [Snapshot Model](../erd/snapshot-model.md) | Snapshot Module |
| FieldValueVersion на каждый successful submit | BR-26, BR-22 | Snapshot Module |
| First-approve wins | BR-03 | Approval Engine |
| Запрет самосогласования | BR-21 | Authorization + Approval Engine |
| Комментарий обязателен reject/return | BR-25 | Approval Engine |
| RBAC / ownership | BR-01, BR-14–16 | Authorization Module |
| История (+ версии значений) | BR-24 | Audit Module |

---

## 6. Границы этапа

ERD / OpenAPI / код / микросервисы / cloud сверх NFR — вне этого индекса. Новые FR/BR/NFR этим файлом не вводятся.

---

## 7. DoD

1. Каталог содержит ARCH-00…ARCH-MAP и ADR Baseline.
2. Context / container / component описаны.
3. Монолит обоснован; решения вне требований помечены ADR.
4. Snapshot — ссылка на Snapshot Model, без дублирования механики.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Stage 3.3 |
| 1.1 | 2026-09-20 | ADR-SNAP-01 / ADR-AUTH-DEMO-01; вариант B |
