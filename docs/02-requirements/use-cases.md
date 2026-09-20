# Пользовательские сценарии (Use Cases)

**Продукт:** Employee Service  
**Документ:** Use Cases  
**ID:** DOC-UC  
**Версия:** 1.0  
**Статус:** Baseline v1.0

MVP Baseline. Сценарии вне Baseline — [docs/backlog.md](../backlog.md).

Нумерация UC детализирует список Vision (разделение Create/Submit и др.).

---

## UC-03 — Browse Service Catalog

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Выбрать услугу (тип заявки) из каталога |
| **Primary actor** | employee |
| **Preconditions** | Аутентификация; роль employee |
| **Trigger** | Открытие каталога |
| **Main flow** | 1. Система показывает активные типы 2. Пользователь открывает описание 3. При необходимости запрашивает схему формы |
| **Alternative flows** | A1. Каталог пуст — HTTP 200, пустой список, пустое состояние UI |
| **Exceptions** | E1. Попытка открыть неактивный тип по прямой ссылке → ошибка |
| **Postconditions** | Выбран тип для создания (опционально) |
| **Related FR** | FR-CAT-01, FR-CAT-02, FR-CAT-03 |
| **Related BR** | BR-10 |

---

## UC-04 — Create Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Создать заявку и заполнить поля (draft) |
| **Primary actor** | employee |
| **Preconditions** | Выбран активный тип; известна схема формы |
| **Trigger** | Команда «Создать заявку» |
| **Main flow** | 1. Система создаёт заявку `draft` 2. Пользователь заполняет поля 3. Сохранение значений 4. Запись в истории |
| **Alternative flows** | A1. Сохранение частично заполненной формы (необязательные поля пустые) |
| **Exceptions** | E1. Тип неактивен → ERR_INACTIVE_TYPE  E2. Валидация → ERR_VALIDATION |
| **Postconditions** | Существует заявка `draft` с инициатором = текущий пользователь |
| **Related FR** | FR-REQ-01, FR-REQ-02 |
| **Related BR** | BR-10, BR-19, BR-24 |

---

## UC-05 — Submit Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Отправить заявку на согласование (первый или повторный submit) |
| **Primary actor** | employee (инициатор) |
| **Preconditions** | Заявка в `draft` или `returned`; пользователь — инициатор |
| **Trigger** | Команда «Отправить» |
| **Main flow** | 1. Валидация полей по **актуальной** схеме типа (BR-26) 2. Проверка маршрута (BR-18) 3. Если `draft` — создание экземпляра маршрута (BR-08) 4. Если `returned` — экземпляр маршрута не меняется (BR-22); `currentStageNumber` → 1 (BR-06) 5. Новая версия схемы и значений полей (номер отправки; BR-26) 6. Статус `in_approval` 7. Создание задач этапа 1 8. История (in-app уведомления — [docs/backlog.md](../backlog.md)). Механика: [Snapshot Model](../03-diagrams/erd/snapshot-model.md) |
| **Alternative flows** | A1. Повторный submit после return — согласование с **первого** этапа RouteInstance (BR-06); создаётся новая версия значений, маршрут не rebuild |
| **Exceptions** | E1. ERR_VALIDATION  E2. ERR_ROUTE_CONFIG  E3. ERR_INVALID_STATE  E4. ERR_INACTIVE_TYPE |
| **Postconditions** | Заявка на согласовании; задачи созданы; данные зафиксированы |
| **Related FR** | FR-REQ-03, FR-REQ-09, FR-APP-01, см. [docs/backlog.md](../backlog.md) |
| **Related BR** | BR-06, BR-08, BR-18, BR-20, BR-22, BR-26, см. [docs/backlog.md](../backlog.md) |

---

## UC-06 — View My Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть список и карточку своей заявки |
| **Primary actor** | employee |
| **Preconditions** | Аутентификация |
| **Trigger** | Открытие «Мои заявки» / карточки |
| **Main flow** | 1. Список своих заявок 2. Открытие карточки 3. Просмотр полей, статуса, этапа, комментариев 4. При необходимости — добавление свободного комментария, в т.ч. в `in_approval` (BR-28) |
| **Alternative flows** | A1. Фильтр по статусу |
| **Exceptions** | E1. Чужой id → ERR_NOT_FOUND |
| **Postconditions** | — |
| **Related FR** | FR-CAB-02, FR-REQ-04, FR-REQ-05, FR-REQ-06 |
| **Related BR** | BR-01, BR-28 |

---

## UC-07 — Approve Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Согласовать текущий этап заявки |
| **Primary actor** | approver |
| **Preconditions** | Есть открытая задача, пользователь — assignee; не инициатор заявки |
| **Trigger** | Действие Approve в карточке задачи |
| **Main flow** | 1. Просмотр **полной** карточки заявки (BR-14) 2. Approve (комментарий необязателен, BR-25) 3. Задача завершена 4. Остальные активные задачи этапа → `cancelled` (BR-03) 5. Если есть следующий этап — создание его задач (FR-APP-06) 6. Если последний — статус `approved` 7. История (in-app уведомления — [docs/backlog.md](../backlog.md)) |
| **Alternative flows** | A1. Несколько assignees — достаточно одного approve (BR-03) |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE  E3. Самосогласование → ERR_FORBIDDEN_APPROVAL (BR-21) |
| **Postconditions** | Этап пройден или заявка `approved` |
| **Related FR** | FR-APP-02, FR-APP-03, FR-APP-06, FR-APP-07 |
| **Related BR** | BR-02, BR-03, BR-14, BR-15, BR-17, BR-21, BR-25, см. [docs/backlog.md](../backlog.md) |

---

## UC-08 — Reject Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Отклонить заявку |
| **Primary actor** | approver |
| **Preconditions** | Открытая задача; assignee; не инициатор |
| **Trigger** | Действие Reject |
| **Main flow** | 1. Reject + **обязательный** комментарий (BR-25) 2. Статус `rejected` 3. Закрытие открытых задач этапа 4. История |
| **Alternative flows** | — |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE  E3. Пустой комментарий → ERR_VALIDATION |
| **Postconditions** | Заявка `rejected`; маршрут завершён |
| **Related FR** | FR-APP-04, FR-AUDIT-02; уведомления — [docs/backlog.md](../backlog.md) |
| **Related BR** | BR-04, BR-15, BR-21, BR-25 |

---

## UC-09 — Return Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Вернуть заявку инициатору на доработку |
| **Primary actor** | approver |
| **Preconditions** | Открытая задача; assignee; не инициатор |
| **Trigger** | Действие Return |
| **Main flow** | 1. Return + **обязательный** комментарий (BR-25) 2. Статус `returned` 3. Фиксация номера этапа возврата (аудит; при resubmit — с первого этапа, BR-06) 4. Закрытие задач этапа 5. История |
| **Alternative flows** | A1. Инициатор далее редактирует (FR-REQ-02) и делает UC-05 |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE  E3. Пустой комментарий → ERR_VALIDATION |
| **Postconditions** | BR-05; заявка доступна инициатору для правки |
| **Related FR** | FR-APP-05, FR-REQ-08, FR-REQ-02, FR-REQ-09 |
| **Related BR** | BR-05, BR-06, BR-15, BR-25 |

---

## UC-10 — Cancel Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Отменить свою заявку |
| **Primary actor** | employee (инициатор) |
| **Preconditions** | Статус `draft` или `returned` |
| **Trigger** | Действие «Отменить» |
| **Main flow** | 1. Подтверждение 2. Статус `cancelled` 3. История |
| **Alternative flows** | — |
| **Exceptions** | E1. Статус иной → ERR_INVALID_STATE |
| **Postconditions** | Заявка `cancelled` |
| **Related FR** | FR-REQ-07 |
| **Related BR** | BR-07 |

---

## UC-14 — View Request History

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть историю действий по заявке |
| **Primary actor** | employee / approver (в рамках прав Baseline; admin-реестр — [docs/backlog.md](../backlog.md)) |
| **Preconditions** | Право на просмотр заявки |
| **Trigger** | Открытие вкладки «История» |
| **Main flow** | 1. Запрос событий 2. Отображение хронологии (кто, когда, действие, from/to, комментарий) |
| **Alternative flows** | — |
| **Exceptions** | E1. Нет доступа → ERR_NOT_FOUND |
| **Postconditions** | — |
| **Related FR** | FR-AUDIT-01, FR-AUDIT-02, см. [docs/backlog.md](../backlog.md) |
| **Related BR** | BR-24 |

---

## Сводка

| ID | Название |
| :--- | :--- |
| UC-03 | Browse Service Catalog |
| UC-04 | Create Request |
| UC-05 | Submit Request |
| UC-06 | View My Request |
| UC-07 | Approve Request |
| UC-08 | Reject Request |
| UC-09 | Return Request |
| UC-10 | Cancel Request |
| UC-14 | View Request History |

**Количество UC (Baseline): 9**  
Backlog UC: см. [docs/backlog.md](../backlog.md).

---

## Open Questions / TBD

**Обязательных открытых вопросов для Baseline нет.**  
Закрытые решения — [business-rules.md](./business-rules.md) §9.

---

## Трассировка

См. таблицы Related FR / Related BR в каждом UC. Обратная трассировка FR→UC — в [functional-requirements.md](./functional-requirements.md).  
Backlog-требования — [docs/backlog.md](../backlog.md).
