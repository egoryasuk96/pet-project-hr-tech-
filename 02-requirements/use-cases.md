# Пользовательские сценарии (Use Cases)

**Проект:** Employee Service  
**Документ:** Use Cases  
**Версия:** 1.0  
**Статус:** Draft (Этап 2)

Нумерация UC Этапа 2 детализирует список Vision (разделение Create/Submit и др.).

---

## UC-01 — Login

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Аутентифицироваться и получить доступ к системе |
| **Primary actor** | Любой пользователь |
| **Preconditions** | Учётная запись существует |
| **Trigger** | Пользователь открывает форму входа и отправляет логин/пароль |
| **Main flow** | 1. Ввод логина и пароля 2. Система проверяет данные 3. Выдаётся JWT 4. Пользователь попадает в соответствующий домашний раздел (ЛК / очередь / админка — по ролям) |
| **Alternative flows** | A1. Несколько ролей — UI показывает доступные разделы |
| **Exceptions** | E1. Неверные данные → сообщение ERR_INVALID_CREDENTIALS, повтор ввода |
| **Postconditions** | Пользователь аутентифицирован |
| **Related FR** | FR-AUTH-01, FR-AUTH-02, FR-AUTH-03 |
| **Related BR** | BR-16 |

---

## UC-02 — View Profile

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть свои персональные данные |
| **Primary actor** | employee (также любой аутентифицированный — свой профиль) |
| **Preconditions** | UC-01 выполнен |
| **Trigger** | Открытие раздела «Профиль» |
| **Main flow** | 1. Запрос профиля 2. Отображение ФИО, email, должность, отдел |
| **Alternative flows** | — |
| **Exceptions** | E1. Сессия истекла → ERR_UNAUTHORIZED, возврат на login |
| **Postconditions** | Данные не изменены |
| **Related FR** | FR-CAB-01, FR-AUTH-02 |
| **Related BR** | — |

---

## UC-03 — Browse Service Catalog

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Выбрать услугу (тип заявки) из каталога |
| **Primary actor** | employee |
| **Preconditions** | Аутентификация; роль employee |
| **Trigger** | Открытие каталога |
| **Main flow** | 1. Система показывает активные типы 2. Пользователь открывает описание 3. При необходимости запрашивает схему формы |
| **Alternative flows** | A1. Каталог пуст — показывается пустое состояние |
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
| **Main flow** | 1. Валидация полей 2. Проверка маршрута (BR-18) 3. Если `draft` — создание snapshot (BR-08) 4. Если `returned` — snapshot не меняется (BR-22) 5. Статус `in_approval` 6. Создание задач текущего этапа 7. Уведомления согласующим 8. История |
| **Alternative flows** | A1. Повторный submit после return — этап тот же, что при return (BR-06) |
| **Exceptions** | E1. ERR_VALIDATION  E2. ERR_ROUTE_CONFIG  E3. ERR_INVALID_STATE  E4. ERR_INACTIVE_TYPE (для первого submit, если тип деактивирован) |
| **Postconditions** | Заявка на согласовании; задачи созданы |
| **Related FR** | FR-REQ-03, FR-REQ-09, FR-APP-01, FR-NOTIF-01 |
| **Related BR** | BR-06, BR-08, BR-18, BR-20, BR-22 |

---

## UC-06 — View My Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть список и карточку своей заявки |
| **Primary actor** | employee |
| **Preconditions** | Аутентификация |
| **Trigger** | Открытие «Мои заявки» / карточки |
| **Main flow** | 1. Список своих заявок 2. Открытие карточки 3. Просмотр полей, статуса, этапа, комментариев |
| **Alternative flows** | A1. Фильтр по статусу |
| **Exceptions** | E1. Чужой id → ERR_NOT_FOUND |
| **Postconditions** | — |
| **Related FR** | FR-CAB-02, FR-REQ-04, FR-REQ-05, FR-REQ-06 |
| **Related BR** | BR-01 |

---

## UC-07 — Approve Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Согласовать текущий этап заявки |
| **Primary actor** | approver |
| **Preconditions** | Есть открытая задача, пользователь — assignee; не инициатор заявки |
| **Trigger** | Действие Approve в карточке задачи |
| **Main flow** | 1. Просмотр заявки 2. Approve (+ опц. комментарий) 3. Задача завершена 4. First-approve: прочие задачи этапа закрыты 5. Если есть следующий этап — UC-переход (FR-APP-06) 6. Если последний — статус `approved` 7. История + уведомления |
| **Alternative flows** | A1. Несколько assignees — достаточно одного approve (BR-03) |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE  E3. Самосогласование → ERR_FORBIDDEN_APPROVAL |
| **Postconditions** | Этап пройден или заявка `approved` |
| **Related FR** | FR-APP-02, FR-APP-03, FR-APP-06, FR-APP-07 |
| **Related BR** | BR-02, BR-03, BR-15, BR-17, BR-21 |

---

## UC-08 — Reject Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Отклонить заявку |
| **Primary actor** | approver |
| **Preconditions** | Открытая задача; assignee; не инициатор |
| **Trigger** | Действие Reject |
| **Main flow** | 1. Reject + комментарий 2. Статус `rejected` 3. Закрытие открытых задач этапа 4. История 5. Уведомление инициатору |
| **Alternative flows** | — |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE  E3. Пустой комментарий → ERR_VALIDATION (если принят OQ-FR-01) |
| **Postconditions** | Заявка `rejected`; маршрут завершён |
| **Related FR** | FR-APP-04, FR-NOTIF-01, FR-AUDIT-02 |
| **Related BR** | BR-04, BR-15, BR-21 |

---

## UC-09 — Return Request

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Вернуть заявку инициатору на доработку |
| **Primary actor** | approver |
| **Preconditions** | Открытая задача; assignee; не инициатор |
| **Trigger** | Действие Return |
| **Main flow** | 1. Return + комментарий 2. Статус `returned` 3. Фиксация текущего этапа для будущего resubmit 4. Закрытие задач этапа 5. История 6. Уведомление инициатору |
| **Alternative flows** | A1. Инициатор далее редактирует (FR-REQ-02) и делает UC-05 |
| **Exceptions** | E1. ERR_FORBIDDEN_APPROVAL  E2. ERR_TASK_DONE |
| **Postconditions** | BR-05; заявка доступна инициатору для правки |
| **Related FR** | FR-APP-05, FR-REQ-08, FR-REQ-02, FR-REQ-09 |
| **Related BR** | BR-05, BR-06 |

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

## UC-11 — Configure Request Type

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Создать или изменить тип заявки и поля формы |
| **Primary actor** | admin |
| **Preconditions** | Роль admin |
| **Trigger** | Работа в разделе типов заявок |
| **Main flow** | 1. Создание/редактирование типа (имя, описание, is_active) 2. CRUD полей формы 3. При необходимости привязка справочников 4. Сохранение |
| **Alternative flows** | A1. Деактивация типа — тип исчезает из каталога (BR-10) |
| **Exceptions** | E1. ERR_VALIDATION  E2. ERR_FORBIDDEN |
| **Postconditions** | Конфигурация сохранена; на запущенные заявки не влияет (BR-09) |
| **Related FR** | FR-ADMIN-01, FR-ADMIN-02, FR-ADMIN-06 |
| **Related BR** | BR-09, BR-10 |

---

## UC-12 — Configure Approval Route

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Настроить последовательный маршрут, этапы и назначения |
| **Primary actor** | admin |
| **Preconditions** | Тип заявки существует; роль admin |
| **Trigger** | Редактирование маршрута типа |
| **Main flow** | 1. Задание этапов и порядка 2. Назначение роли и/или пользователей на каждый этап 3. Сохранение |
| **Alternative flows** | A1. Изменение маршрута после того, как заявки уже запущены — влияет только на новые submit |
| **Exceptions** | E1. Некорректные назначения → ERR_VALIDATION |
| **Postconditions** | Маршрут сохранён; BR-02, BR-09, BR-12 |
| **Related FR** | FR-ADMIN-03, FR-ADMIN-04, FR-ADMIN-05 |
| **Related BR** | BR-02, BR-09, BR-12, BR-18 |

---

## UC-13 — View Notifications

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть in-app уведомления и отметить прочитанными |
| **Primary actor** | Любой аутентифицированный пользователь |
| **Preconditions** | Аутентификация |
| **Trigger** | Открытие раздела уведомлений |
| **Main flow** | 1. Список своих уведомлений 2. Открытие/прочтение 3. Mark as read |
| **Alternative flows** | A1. Переход к связанной заявке/задаче из уведомления |
| **Exceptions** | E1. Чужое уведомление → ERR_NOT_FOUND |
| **Postconditions** | Выбранные уведомления прочитаны |
| **Related FR** | FR-NOTIF-01, FR-NOTIF-02, FR-NOTIF-03, FR-CAB-03 |
| **Related BR** | BR-11, BR-23 |

---

## UC-14 — View Request History

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть историю действий по заявке |
| **Primary actor** | employee / approver / admin (в рамках прав) |
| **Preconditions** | Право на просмотр заявки |
| **Trigger** | Открытие вкладки «История» |
| **Main flow** | 1. Запрос событий 2. Отображение хронологии (кто, когда, действие, from/to, комментарий) |
| **Alternative flows** | — |
| **Exceptions** | E1. Нет доступа → ERR_NOT_FOUND |
| **Postconditions** | — |
| **Related FR** | FR-AUDIT-01, FR-AUDIT-02, FR-ADMIN-08 |
| **Related BR** | BR-24 |

---

## UC-15 — Admin View Requests

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Просмотреть реестр всех заявок |
| **Primary actor** | admin |
| **Preconditions** | Роль admin |
| **Trigger** | Открытие реестра в админке |
| **Main flow** | 1. Список всех заявок с фильтрами 2. Открытие карточки 3. При необходимости — история (UC-14) |
| **Alternative flows** | A1. Фильтр по статусу/типу |
| **Exceptions** | E1. ERR_FORBIDDEN для не-admin |
| **Postconditions** | — |
| **Related FR** | FR-ADMIN-07, FR-ADMIN-08, FR-REQ-04 |
| **Related BR** | BR-13 |

---

## Сводка

| ID | Название |
| :--- | :--- |
| UC-01 | Login |
| UC-02 | View Profile |
| UC-03 | Browse Service Catalog |
| UC-04 | Create Request |
| UC-05 | Submit Request |
| UC-06 | View My Request |
| UC-07 | Approve Request |
| UC-08 | Reject Request |
| UC-09 | Return Request |
| UC-10 | Cancel Request |
| UC-11 | Configure Request Type |
| UC-12 | Configure Approval Route |
| UC-13 | View Notifications |
| UC-14 | View Request History |
| UC-15 | Admin View Requests |

**Количество UC: 15**

---

## Open Questions

| ID | Вопрос | Предложение |
| :--- | :--- | :--- |
| OQ-UC-01 | Домашняя страница после login при нескольких ролях | Экран-выбор раздела или ЛК по умолчанию |
| OQ-UC-02 | Обязательность комментария reject/return | Обязателен |

---

## Трассировка

См. таблицы Related FR / Related BR в каждом UC. Обратная трассировка FR→UC — в [functional-requirements.md](./functional-requirements.md) §11.
