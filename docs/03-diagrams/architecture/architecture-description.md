# Архитектура Employee Service (логико-техническая модель)

**Проект:** Employee Service  
**Этап:** 3.3 — Architecture  
**Версия:** 1.0  
**Статус:** Draft  
**Источник требований:** Этап 1–2 (`01-vision-and-scope/`, `02-requirements/`)  
**Связанные слои:** Этап 3.1 ([BPMN](../bpmn/bpmn-description.md)), Этап 3.2 ([UML](../uml/uml-description.md))

---

## 1. Назначение

Документ фиксирует **логическую и техническую архитектуру** MVP Employee Service на уровне системного аналитика: границы системы, контейнеры (frontend / backend / database), логические компоненты, потоки данных, зоны ответственности, место ключевых бизнес-правил, безопасность, ошибки, аудит и уведомления, ограничения масштабируемости и производительности.

Новые бизнес-правила **не вводятся**. Существующие FR / BR / UC / AC / RBAC / NFR **не изменяются**.

Архитектура **реализует** уже зафиксированные процессы (BPMN) и аналитические взаимодействия (UML), не заменяя их.

---

## 2. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; визуал — встроенный Mermaid |
| **Язык** | Русский |
| **Трассировка** | В каждом файле — ссылки на UC / FR / BR / AC / NFR / RBAC |
| **Требование vs ADR** | То, что явно задано в Stage 1–3.2, цитируется как требование. Технические решения, не зафиксированные как FR/BR/NFR, помечаются как **ADR / предположение MVP** |
| **Логические модули** | Имена модулей backend/SPA — **архитектурное разбиение** монолита, не микросервисы и не новые требования |
| **ERD / OpenAPI / код** | Вне Этапа 3.3 |
| **Deployment / cloud** | Только уровень, уже заданный NFR (Docker Compose, HTTPS для внешнего демо); без K8s/cloud-топологии |

### 2.1. Как читать «требование» и «ADR»

| Метка | Смысл |
| :--- | :--- |
| **Требование** | Уже есть в Vision / FR / BR / NFR / AC / RBAC / BPMN / UML |
| **ADR (MVP)** | Архитектурное решение или предположение реализации; **не** создаёт новый FR/BR/NFR |

Примеры ADR (детали — в файлах этапа):

- состав логических модулей монолита и UI-зон SPA;
- способ хранения JWT на клиенте;
- выбор конкретного password hashing algorithm среди допустимых NFR-SEC-03;
- детализация границ транзакций по модулям (поверх уже требуемой атомарности BR-29 / NFR-REL-01).

Уже зафиксированные ограничения (не ADR): отсутствие refresh token (NFR-SEC-04), in-app only (BR-11), уведомление в одной транзакции с событием (BR-29), stateless API (NFR-SCL-01).

---

## 3. Архитектурный стиль (ADR)

**Выбор:** модульный монолит — один backend deployable + SPA + одна БД.

**Обоснование (не новое требование):**

- один bounded context (заявки и согласование);
- обязательная атомарность status + tasks + history + notifications (BR-29, NFR-REL-01);
- объём MVP и отсутствие независимых команд/SLA на отдельные сервисы;
- Vision уже задаёт единый технический контур: PostgreSQL, FastAPI, React, Docker Compose.

**Микросервисы не предлагаются** для MVP: они усложнили бы транзакционные границы без выгоды из требований.

---

## 4. Список артефактов

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ARCH-00 | [architecture-description.md](./architecture-description.md) | Индекс, соглашения, ADR-стиль, DoD |
| ARCH-CTX | [context-diagram.md](./context-diagram.md) | Граница системы и актёры |
| ARCH-CNT | [container-diagram.md](./container-diagram.md) | Web / API / DB |
| ARCH-CMP | [component-diagram.md](./component-diagram.md) | Логические модули и UI-зоны |
| ARCH-FLOW | [data-flows.md](./data-flows.md) | Потоки submit / approval / admin / audit+notif |
| ARCH-SEC | [security-and-crosscutting.md](./security-and-crosscutting.md) | AuthN/AuthZ, ошибки, логи, NFR, транзакции |
| ARCH-MAP | [architecture-traceability.md](./architecture-traceability.md) | Трассировка и критичные BR |

---

## 5. Сводка: критичные правила → владелец

| Правило | Источник | Архитектурный владелец |
| :--- | :--- | :--- |
| Route snapshot только при первом submit | BR-08, BR-22 | Snapshot Module (оркестрация Submit) |
| Schema/value snapshot при каждом успешном submit | BR-26, BR-22 | Snapshot Module |
| First-approve wins | BR-03 | Approval Engine |
| Запрет самосогласования | BR-21 | Authorization + Approval Engine |
| Комментарий обязателен reject/return | BR-25 | Approval Engine |
| RBAC / ownership | BR-01, BR-13–16, ACL-* | Authorization Module |
| История | BR-24, NFR-LOG-02 | Audit Module (та же TX) |
| In-app notifications | BR-11, BR-23, BR-29 | Notification Module (та же TX) |

Детализация — [architecture-traceability.md](./architecture-traceability.md), [data-flows.md](./data-flows.md).

---

## 6. Что не входит в Этап 3.3

| Тема | Причина |
| :--- | :--- |
| ERD / физическая схема БД | Отдельный этап (`03-diagrams/erd/`) |
| OpenAPI / HTTP paths / DTO | Этап API |
| Код и тесты | Реализация позже |
| Микросервисная топология | Не следует из требований MVP |
| Cloud / K8s / CDN | Не следует из NFR (кроме Compose и HTTPS внешнего демо) |
| Новые FR / BR / NFR | Запрещено |
| Изменение Stage 1–3.2 | Запрещено |

---

## 7. Критерии готовности (DoD)

1. Каталог `03-diagrams/architecture/` содержит все файлы ARCH-00…ARCH-MAP.
2. Есть context, container, component (Mermaid) и описание границ FE / BE / DB.
3. Зафиксирован модульный монолит и обоснование.
4. Технические решения вне Stage 1–3.2 помечены как **ADR / предположение MVP**.
5. Для критичных правил указаны модуль-владелец и транзакционная граница.
6. Внешние runtime-системы не введены сверх требований.
7. Нет ERD, OpenAPI paths, кода, cloud-инфры сверх NFR.
8. Нет новых/изменённых FR/BR/UC/AC/RBAC/NFR.
9. Трассировка компонент ↔ FR/BR/NFR присутствует.
10. README ссылается на Stage 3.3.

---

## 8. Связанные артефакты

- [Vision & Scope](../../01-vision-and-scope/vision-scope.md)
- [Глоссарий](../../01-vision-and-scope/glossary.md)
- [functional-requirements.md](../../02-requirements/functional-requirements.md)
- [business-rules.md](../../02-requirements/business-rules.md)
- [non-functional-requirements.md](../../02-requirements/non-functional-requirements.md)
- [error-matrix.md](../../02-requirements/error-matrix.md)
- [rbac-matrix.md](../../02-requirements/rbac-matrix.md)
- [bpmn-description.md](../bpmn/bpmn-description.md)
- [uml-description.md](../uml/uml-description.md)

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Stage 3.3 Architecture |
