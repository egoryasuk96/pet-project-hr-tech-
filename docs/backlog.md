# Backlog требований (вне текущего MVP-среза / исторические тексты)

**Продукт:** Employee Service  
**ID документа:** DOC-BACKLOG  
**Статус:** Backlog + Target-active markers  
**Версия:** 1.2  
**Связанный Baseline:** [docs/02-requirements/](./02-requirements/)

Документ хранит полный исходный текст требований, вынесенных из раннего MVP Baseline.  
ID не удаляются и не перенумеровываются — они сохранены для трассировки и будущего scope.

> **Frozen Target (2026-09-24):** **Target-active / Delivered** (не backlog): JWT login `/auth/login` + `/me` (UC-01, FR-AUTH-01…03, AC-AUTH-01, NFR-SEC-01/03/04); RBAC одна `role_id` (BR-16); создание/лист in-app notifications (FR-NOTIF-01/02, BR-11/23/29, AC-NOTIF-01; UC-13 list). Action Engine / live-route — в Baseline/Target API, не в этом backlog.  
> **Остаётся backlog:** Admin UI/API, Cabinet/профиль, Create UI, Approver Queue, mark-as-read (FR-NOTIF-03), free comments, change-password, multi-instance (NFR-SCL-01).  
> Тела ниже могут содержать **Legacy wording** (multi-role / ЛК) — не CURRENT; смотри пометки у разделов.

> Замечание: в теле backlog-требований могут встречаться ссылки на Baseline ID (это нормально). Baseline-файлы не должны содержать backlog ID в Related/Связи/трассировке без отсылки сюда.

---

## Сводка перенесённых ID

| Тип | ID | Причина / статус |
| :--- | :--- | :--- |
| UC | UC-01 | Login/JWT — **Target-active**; Legacy wording в теле |
| UC | UC-02 | Профиль / ЛК — backlog |
| UC | UC-11 | Админ-настройка типов — backlog |
| UC | UC-12 | Админ-настройка маршрутов — backlog |
| UC | UC-13 | List notifications — **Target-active**; mark-as-read в теле — Legacy / FR-NOTIF-03 backlog |
| UC | UC-15 | Админ-реестр — backlog |
| FR | FR-ADMIN-01…08 | Админ-панель / реестр — backlog |
| FR | FR-AUTH-01 | JWT/логин — **Target-active**; Legacy wording |
| FR | FR-AUTH-02 | `/me` / сессия JWT — **Target-active**; Legacy wording (роли plural) |
| FR | FR-AUTH-03 | AuthZ через JWT + `role_id` — **Target-active**; Legacy wording (union roles) |
| FR | FR-CAB-01 | Профиль — backlog |
| FR | FR-CAB-03 | Уведомления в кабинете — backlog (Cabinet UI) |
| FR | FR-NOTIF-01 | Создание in-app — **Target-active** |
| FR | FR-NOTIF-02 | Список уведомлений — **Target-active** |
| FR | FR-NOTIF-03 | Mark as read — **backlog** (не Target contract) |
| BR | BR-11 | In-app only — **Target-active** |
| BR | BR-13 | Реестр admin — backlog |
| BR | BR-23 | События уведомлений — **Target-active** |
| BR | BR-27 | Правило admin — backlog |
| BR | BR-29 | Атомарность уведомлений — **Target-active** |
| AC | AC-ACC-04 | Админка — backlog |
| AC | AC-ACC-05 | Реестр admin — backlog |
| AC | AC-ADMIN-01 | Активация типа admin — backlog |
| AC | AC-AUTH-01 | Login — **Target-active**; Legacy wording (multi-role) |
| AC | AC-NOTIF-01 | TX уведомления — **Target-active** |
| NFR | NFR-SCL-01 | Multi-instance — backlog |
| NFR | NFR-SEC-01 | JWT AuthN — **Target-active** |
| NFR | NFR-SEC-03 | Password hash — **Target-active** |
| NFR | NFR-SEC-04 | TTL токена — **Target-active** |

**Итого ID в файле (исторический инвентарь):** UC 6 + FR 16 + BR 5 + AC 5 + NFR 4 = **36** (часть — Target-active, не deferred scope).

**Итого Baseline:** UC 9 + FR 22 + BR 24 + AC 27 + NFR 25 = **107**

**Инвентарь всего:** 15 + 38 + 29 + 32 + 29 = **143**

---

## Use Cases (backlog)

### UC-01

**Статус:** Target-active (Delivered) — `POST /auth/login`, JWT Bearer; см. ADR-AUTH-JWT-01.  
**Legacy wording:** main flow / A1 / postconditions описывают multi-role и ЛК. **Target wording:** одна `User.role_id`; после login — My Requests (не полный ЛК).

## UC-01 — Login

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Аутентифицироваться и получить доступ к системе |
| **Primary actor** | Любой пользователь |
| **Preconditions** | Учётная запись существует |
| **Trigger** | Пользователь открывает форму входа и отправляет логин/пароль |
| **Main flow** | 1. Ввод логина и пароля 2. Система проверяет данные 3. Выдаётся JWT (TTL 8 часов) со списком всех ролей 4. Отображается **ЛК**; доступна навигация ко всем разделам по объединению permissions (BR-16); выбор активной роли не выполняется |
| **Alternative flows** | A1. Несколько ролей — в навигации одновременно ЛК, очередь согласования, админка (если роли это позволяют) |
| **Exceptions** | E1. Неверные данные → сообщение ERR_INVALID_CREDENTIALS, повтор ввода |
| **Postconditions** | Пользователь аутентифицирован; видит ЛК |
| **Related FR** | FR-AUTH-01, FR-AUTH-02, FR-AUTH-03 |
| **Related BR** | BR-16 |

---

---

### UC-02

**Причина выноса:** Профиль / ЛК — Vision §7.1

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

---

### UC-11

**Причина выноса:** Админ-настройка типов — Vision §7.1

## UC-11 — Configure Request Type

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Создать или изменить тип заявки и поля формы |
| **Primary actor** | admin |
| **Preconditions** | Роль admin |
| **Trigger** | Работа в разделе типов заявок |
| **Main flow** | 1. Создание/редактирование типа (имя, описание, is_active) 2. CRUD полей формы 3. При необходимости привязка справочников 4. При активации — проверка валидности маршрута (BR-18) 5. Сохранение |
| **Alternative flows** | A1. Деактивация типа — тип исчезает из каталога (BR-10) |
| **Exceptions** | E1. ERR_VALIDATION  E2. ERR_FORBIDDEN  E3. Активация при невалидном маршруте → ERR_ROUTE_CONFIG |
| **Postconditions** | Конфигурация сохранена; in-flight caveat — правки live config **могут** затронуть незавершённые заявки ([ADR-LIVE-CFG-01](./03-diagrams/architecture/adr-live-config.md), BR-09 guard); draft/returned при edit видят актуальную схему (BR-26) |
| **Related FR** | FR-ADMIN-01, FR-ADMIN-02, FR-ADMIN-06 |
| **Related BR** | BR-09, BR-10, BR-18, BR-26, BR-27 |

---

---

### UC-12

**Причина выноса:** Админ-настройка маршрутов — Vision §7.1

## UC-12 — Configure Approval Route

| Поле | Содержание |
| :--- | :--- |
| **Goal** | Настроить последовательный маршрут, этапы и назначения |
| **Primary actor** | admin |
| **Preconditions** | Тип заявки существует; роль admin |
| **Trigger** | Редактирование маршрута типа |
| **Main flow** | 1. Задание этапов и порядка 2. Назначение роли и/или пользователей на каждый этап 3. Сохранение 4. При активации связанного типа — валидация маршрута (BR-18) |
| **Alternative flows** | A1. Изменение маршрута после того, как заявки уже запущены — влияет только на новые submit |
| **Exceptions** | E1. Некорректные назначения → ERR_VALIDATION  E2. Попытка активировать тип с невалидным маршрутом → ERR_ROUTE_CONFIG |
| **Postconditions** | Маршрут сохранён; BR-02, BR-09, BR-12, BR-18 |
| **Related FR** | FR-ADMIN-03, FR-ADMIN-04, FR-ADMIN-05 |
| **Related BR** | BR-02, BR-09, BR-12, BR-18 |

---

---

### UC-13

**Статус:** Target-active (list) — `GET /notifications`, FR-NOTIF-02. Создание на событиях — FR-NOTIF-01 / BR-23/29.  
**Остаётся backlog:** mark-as-read (шаг 3 / FR-NOTIF-03); Cabinet entry (FR-CAB-03).  
**Legacy wording:** goal/postconditions предполагают mark-as-read как обязательный шаг.

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

---

### UC-15

**Причина выноса:** Админ-реестр — Vision §7.1

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

---

## Functional Requirements (backlog)

### FR-ADMIN-01

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-01 — Управление типами заявок
| Поле | Содержание |
| :--- | :--- |
| **Название** | CRUD типов заявок |
| **Описание** | Admin создаёт/читает/изменяет типы; активация (`is_active = true`) допускается только при валидном маршруте (BR-18) |
| **Actor** | admin |
| **Preconditions** | Роль admin |
| **Основной сценарий** | Стандартный CRUD; при активации — проверка маршрута; деактивация через is_active=false (BR-10) |
| **Альтернативы / исключения** | ERR_VALIDATION; ERR_FORBIDDEN; невалидный маршрут при активации → ERR_ROUTE_CONFIG |
| **Postconditions** | Live config caveat (ADR-LIVE-CFG-01); admin не создаёт заявки от сотрудников (BR-27) |
| **Связи** | UC-11; BR-09, BR-10, BR-18, BR-27; AC-ADMIN-01 |

---

### FR-ADMIN-02

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-02 — Управление полями типов
| Поле | Содержание |
| :--- | :--- |
| **Название** | CRUD полей формы типа |
| **Описание** | Admin задаёт поля: код, название, тип, обязательность, порядок, справочник |
| **Actor** | admin |
| **Preconditions** | Тип существует |
| **Основной сценарий** | CRUD полей |
| **Альтернативы / исключения** | ERR_VALIDATION (дубликат кода поля) |
| **Postconditions** | При edit draft/returned клиенты получают актуальную схему (BR-26); working values — единственный носитель значений; in-flight caveat ADR-LIVE-CFG-01 |
| **Связи** | UC-11; FR-CAT-03; BR-26; AC-DRAFT-01, AC-DRAFT-02 |

---

### FR-ADMIN-03

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-03 — Управление маршрутами
| Поле | Содержание |
| :--- | :--- |
| **Название** | Настройка маршрута типа |
| **Описание** | Admin связывает тип с маршрутом и управляет его составом |
| **Actor** | admin |
| **Preconditions** | Тип существует |
| **Основной сценарий** | Создание/изменение маршрута типа |
| **Альтернативы / исключения** | — |
| **Postconditions** | BR-09 |
| **Связи** | UC-12; BR-02 |

---

### FR-ADMIN-04

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-04 — Управление этапами
| Поле | Содержание |
| :--- | :--- |
| **Название** | CRUD этапов и порядка |
| **Описание** | Admin задаёт этапы и последовательность (sequence) |
| **Actor** | admin |
| **Preconditions** | Маршрут существует |
| **Основной сценарий** | Добавление/удаление/переупорядочивание этапов |
| **Альтернативы / исключения** | Пустой/невалидный маршрут блокирует активацию типа и submit (BR-18) |
| **Postconditions** | Порядок этапов определён |
| **Связи** | UC-12; BR-02, BR-18; AC-ADMIN-01 |

---

### FR-ADMIN-05

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-05 — Управление назначениями
| Поле | Содержание |
| :--- | :--- |
| **Название** | Назначение ролей/пользователей на этап |
| **Описание** | Admin назначает на этап роль и/или пользователя явно (BR-12) |
| **Actor** | admin |
| **Preconditions** | Этап существует |
| **Основной сценарий** | CRUD назначений |
| **Альтернативы / исключения** | Назначение несуществующего пользователя → ERR_VALIDATION |
| **Postconditions** | BR-12 |
| **Связи** | UC-12 |

---

### FR-ADMIN-06

**Причина выноса:** Админ-панель — Vision §7.1

### FR-ADMIN-06 — Управление справочниками
| Поле | Содержание |
| :--- | :--- |
| **Название** | CRUD справочников и элементов |
| **Описание** | Admin управляет справочниками и значениями (код, имя, is_active) |
| **Actor** | admin |
| **Preconditions** | Роль admin |
| **Основной сценарий** | CRUD |
| **Альтернативы / исключения** | ERR_VALIDATION |
| **Postconditions** | Активные элементы доступны в формах |
| **Связи** | UC-11 |

---

### FR-ADMIN-07

**Причина выноса:** Админ-реестр — Vision §7.1

### FR-ADMIN-07 — Реестр заявок
| Поле | Содержание |
| :--- | :--- |
| **Название** | Просмотр всех заявок |
| **Описание** | Admin просматривает реестр заявок с фильтром по статусу/типу и пагинацией |
| **Actor** | admin |
| **Preconditions** | Роль admin |
| **Основной сценарий** | 1) Открытие реестра 2) Список всех заявок |
| **Альтернативы / исключения** | — |
| **Postconditions** | — |
| **Связи** | BR-13; UC-15 |

---

### FR-ADMIN-08

**Причина выноса:** Админ-история — Vision §7.1

### FR-ADMIN-08 — Просмотр истории (админ)
| Поле | Содержание |
| :--- | :--- |
| **Название** | История любой заявки |
| **Описание** | Admin открывает историю выбранной заявки |
| **Actor** | admin |
| **Preconditions** | Роль admin |
| **Основной сценарий** | Делегирует FR-AUDIT-01 с правом admin |
| **Альтернативы / исключения** | ERR_NOT_FOUND |
| **Postconditions** | — |
| **Связи** | UC-14, UC-15 |

---

---

### FR-AUTH-01

**Статус:** Target-active (Delivered) — `POST /auth/login`.  
**Legacy wording:** «полный список ролей», ЛК, union permissions. **Target wording:** JWT + одна `role_id` (BR-16); UI → My Requests.

### FR-AUTH-01 — Вход в систему
| Поле | Содержание |
| :--- | :--- |
| **Название** | Вход по логину и паролю |
| **Описание** | Пользователь аутентифицируется логином и паролем и получает JWT для последующих запросов |
| **Actor** | Любой зарегистрированный пользователь |
| **Preconditions** | Учётная запись существует и активна |
| **Основной сценарий** | 1) Ввод логина и пароля 2) Система проверяет данные 3) Выдаётся JWT (TTL = 8 часов, NFR-SEC-04) и данные пользователя, включая **полный список ролей** 4) Отображается ЛК; клиент предоставляет навигацию ко всем разделам по объединению permissions (BR-16); выбор активной роли не требуется |
| **Альтернативы / исключения** | Неверные данные → ERR_INVALID_CREDENTIALS; неактивный пользователь → ERR_FORBIDDEN |
| **Postconditions** | Клиент хранит токен; пользователь считается аутентифицированным до expiry |
| **Связи** | UC-01; NFR-SEC-01, NFR-SEC-04; BR-16; AC-AUTH-01; ERR_INVALID_CREDENTIALS |

---

### FR-AUTH-02

**Статус:** Target-active (Delivered) — `GET /me`.  
**Legacy wording:** «роли» (plural). **Target wording:** одна системная роль `role_id`.

### FR-AUTH-02 — Текущий пользователь
| Поле | Содержание |
| :--- | :--- |
| **Название** | Получение текущего пользователя |
| **Описание** | Аутентифицированный пользователь получает свой профиль сессии: id, ФИО, email, должность, отдел, роли |
| **Actor** | Аутентифицированный пользователь |
| **Preconditions** | Валидный JWT |
| **Основной сценарий** | 1) Клиент запрашивает текущего пользователя 2) Система возвращает данные по subject токена |
| **Альтернативы / исключения** | Нет/невалидный токен → ERR_UNAUTHORIZED |
| **Postconditions** | Данные не изменяются |
| **Связи** | UC-01, UC-02; FR-CAB-01 |

---

### FR-AUTH-03

**Статус:** Target-active (Delivered) — AuthZ на backend после JWT.  
**Legacy wording:** «роли (union)». **Target wording:** одна `User.role_id` + ownership (BR-16).

### FR-AUTH-03 — Авторизация по ролям и правилам
| Поле | Содержание |
| :--- | :--- |
| **Название** | Проверка прав на операцию |
| **Описание** | Перед выполнением операции система проверяет роли (union) и ограничения владения/assignee (RBAC, BR-01, BR-13–16, BR-21) |
| **Actor** | Система |
| **Preconditions** | Аутентифицированный запрос |
| **Основной сценарий** | 1) Определяются роли пользователя 2) Проверяется разрешение функции 3) При необходимости проверяется владение ресурсом / assignee 4) Операция выполняется |
| **Альтернативы / исключения** | Нет прав → ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL / ERR_NOT_FOUND |
| **Postconditions** | При отказе состояние не меняется |
| **Связи** | RBAC; AC-ACC-*; все защищённые FR |

---

## 2. CAB — Личный кабинет

---

### FR-CAB-01

**Причина выноса:** Профиль — Vision §7.1

### FR-CAB-01 — Просмотр профиля
| Поле | Содержание |
| :--- | :--- |
| **Название** | Просмотр профиля сотрудника |
| **Описание** | Пользователь просматривает свои персональные данные: ФИО, email, должность, отдел |
| **Actor** | employee (также любой аутентифицированный пользователь — свои данные) |
| **Preconditions** | Аутентификация |
| **Основной сценарий** | 1) Открывает раздел профиля 2) Система показывает атрибуты пользователя |
| **Альтернативы / исключения** | ERR_UNAUTHORIZED |
| **Postconditions** | Данные не изменяются |
| **Связи** | UC-02; Vision scope §2 |

---

### FR-CAB-03

**Причина выноса:** Уведомления в кабинете — Vision §7.1

### FR-CAB-03 — Просмотр уведомлений в кабинете
| Поле | Содержание |
| :--- | :--- |
| **Название** | Доступ к in-app уведомлениям |
| **Описание** | Пользователь открывает список своих уведомлений из личного кабинета |
| **Actor** | Любой аутентифицированный пользователь |
| **Preconditions** | Аутентификация |
| **Основной сценарий** | См. FR-NOTIF-02 |
| **Альтернативы / исключения** | — |
| **Postconditions** | — |
| **Связи** | FR-NOTIF-02; UC-13; BR-11 |

---

## NOTIF — Уведомления

### FR-NOTIF-01

**Статус:** Target-active (Delivered) — создание в TX с бизнес-событием.

### FR-NOTIF-01 — Создание in-app уведомления
| Поле | Содержание |
| :--- | :--- |
| **Название** | Создание уведомления |
| **Описание** | Система создаёт in-app уведомление получателю при событиях BR-23 **в одной транзакции** с бизнес-событием (BR-29) |
| **Actor** | Система |
| **Preconditions** | Произошло бизнес-событие |
| **Основной сценарий** | 1) В той же транзакции: бизнес-изменение + создание уведомления(й) 2) Commit |
| **Альтернативы / исключения** | Сбой уведомления → полный rollback бизнес-изменения |
| **Postconditions** | Уведомление доступно получателю |
| **Связи** | BR-11, BR-23, BR-29; UC-13; AC-NOTIF-01 |

---

### FR-NOTIF-02

**Статус:** Target-active (Delivered) — `GET /notifications`.

### FR-NOTIF-02 — Просмотр уведомлений
| Поле | Содержание |
| :--- | :--- |
| **Название** | Список уведомлений |
| **Описание** | Пользователь видит свои уведомления (новые и прочитанные), пагинация |
| **Actor** | Аутентифицированный пользователь |
| **Preconditions** | Аутентификация |
| **Основной сценарий** | 1) Открытие списка 2) Выдача только своих уведомлений |
| **Альтернативы / исключения** | — |
| **Postconditions** | — |
| **Связи** | FR-CAB-03; UC-13 |

---

### FR-NOTIF-03

**Статус:** backlog — mark-as-read **не** входит в Frozen Target API contract.

### FR-NOTIF-03 — Отметка прочитанным
| Поле | Содержание |
| :--- | :--- |
| **Название** | Mark as read |
| **Описание** | Пользователь отмечает своё уведомление прочитанным |
| **Actor** | Владелец уведомления |
| **Preconditions** | Уведомление существует и принадлежит пользователю |
| **Основной сценарий** | 1) Действие read 2) Флаг read=true |
| **Альтернативы / исключения** | Чужое → ERR_NOT_FOUND; уже прочитано → идемпотентный успех |
| **Postconditions** | Уведомление прочитано |
| **Связи** | UC-13 |

---

## Business Rules (backlog / Target-active)

### BR-11

**Статус:** Target-active — только in-app (email/push out of scope).

### BR-11 — Уведомления только in-app
В MVP уведомления доставляются только внутри приложения. Email и push не используются.  
**Связи:** FR-NOTIF-01–03, UC-13

---

### BR-13

**Причина выноса:** Реестр admin — Vision §7.1

### BR-13 — Видимость заявок администратора
Администратор (`admin`) может просматривать реестр всех заявок и историю по любой заявке.  
**Связи:** FR-ADMIN-07, FR-ADMIN-08, UC-15, UC-14

---

### BR-23

**Статус:** Target-active — события создания уведомлений в runtime.

### BR-23 — Обязательные события уведомлений
Система создаёт in-app уведомление как минимум при: назначении новой задачи согласующему; смене статуса заявки для инициатора (в т.ч. approve этапа / reject / return / approved / cancelled — по факту события).  
**Связи:** FR-NOTIF-01

---

### BR-27

**Причина выноса:** Правило admin — Vision §7.1 (Admin UI — backlog)

### BR-27 — Admin не создаёт заявки от имени сотрудника
В MVP администратор не создаёт и не отправляет заявки от имени сотрудника. Создание заявок — только роль `employee` (инициатор).  
**Связи:** FR-REQ-01, FR-ADMIN-07, RBAC, UC-04, UC-15

---

### BR-29

**Статус:** Target-active — уведомление в одной TX с бизнес-событием.

### BR-29 — Атомарность in-app уведомления
Создание in-app уведомления выполняется **в одной транзакции** с соответствующим бизнес-событием. Если фиксация уведомления не удалась, откатывается и бизнес-изменение.  
**Связи:** FR-NOTIF-01, BR-23, NFR-REL-01

---

## Acceptance Criteria (backlog / Target-active)

### AC-ACC-04

**Причина выноса:** Админка — Vision §7.1

### AC-ACC-04 — Админка только для admin; admin не создаёт заявки от сотрудника
**Related:** FR-ADMIN-01, FR-REQ-01, BR-27; ACL-04 / ACL-09 — определить в rbac-matrix при возврате admin в scope ([consistency-review.md](./consistency-review.md) RR-ACL-01)

Given пользователь без роли `admin`  
When он пытается создать/изменить тип заявки  
Then ERR_FORBIDDEN

Given пользователь только с ролью `admin` (без `employee`)  
When он пытается создать заявку  
Then операция недоступна (нет права создания заявки; ERR_FORBIDDEN)

---

### AC-ACC-05

**Причина выноса:** Реестр admin — Vision §7.1

### AC-ACC-05 — Admin видит реестр
**Related:** FR-ADMIN-07, BR-13

Given пользователь с ролью `admin`  
When он открывает реестр заявок  
Then он видит заявки всех инициаторов

---

### AC-ADMIN-01

**Причина выноса:** Активация типа admin — Vision §7.1

### AC-ADMIN-01 — Активация типа с невалидным маршрутом запрещена
**Related:** FR-ADMIN-01, FR-ADMIN-03–04, BR-18

Given тип заявки с маршрутом без этапов или без назначений  
When администратор пытается установить `is_active = true`  
Then ERR_ROUTE_CONFIG (или ERR_VALIDATION)  
And тип остаётся неактивным

---

### AC-AUTH-01

**Статус:** Target-active (login delivered).  
**Legacy wording:** Given/Then про несколько ролей и ЛК. **Target wording:** одна `role_id`; после login — My Requests.

### AC-AUTH-01 — Login при нескольких ролях
**Related:** FR-AUTH-01, BR-16

Given пользователь имеет роли `employee` и `approver`  
When он успешно входит  
Then отображается ЛК  
And в навигации доступны разделы, разрешённые объединением ролей  
And отдельный выбор активной роли не предлагается

---

---

### AC-NOTIF-01

**Статус:** Target-active — создание уведомления в одной TX (FR-NOTIF-01 / BR-29).

### AC-NOTIF-01 — Уведомление в одной транзакции
**Related:** FR-NOTIF-01, BR-29

Given бизнес-событие (например submit), создающее уведомление  
When транзакция успешно завершается  
Then и изменение заявки, и уведомление сохранены  
When создание уведомления падает внутри транзакции  
Then откатывается и бизнес-изменение (заявка не остаётся в промежуточном состоянии без уведомления)

---

## Non-Functional Requirements (backlog / Target-active)

### NFR-SCL-01

**Причина выноса:** Multi-instance вне MVP — отложено

### NFR-SCL-01 — Готовность к нескольким экземплярам API
Multi-instance deployment **не входит в MVP**. Архитектура API должна оставаться **stateless** (JWT, без server-side session store), чтобы не создавать искусственных ограничений для последующего перехода к нескольким экземплярам. Фактический деплой ≥2 инстансов в MVP не требуется.  
**Проверка:** архитектурный review — отсутствие sticky session / server session store.

---

### NFR-SEC-01

**Статус:** Target-active (Delivered) — JWT Bearer на защищённых операциях.

### NFR-SEC-01 — Аутентификация
Доступ к защищённым операциям возможен только с валидным JWT. Невалидный/просроченный токен → HTTP 401.  
**Проверка:** запросы без токена и с битым токеном.

---

### NFR-SEC-03

**Статус:** Target-active (Delivered) — bcrypt hash.

### NFR-SEC-03 — Хранение паролей
Пароли хранятся только в виде безопасного password hash. Используется **bcrypt** или эквивалентный современный password hashing algorithm (например argon2). Plain-text запрещён.  
**Проверка:** инспекция БД / unit-тест хеширования.

---

### NFR-SEC-04

**Статус:** Target-active (Delivered) — TTL 8h; refresh отсутствует.

### NFR-SEC-04 — Срок жизни токена
Access token TTL = **8 часов**. Refresh tokens в MVP отсутствуют (повторный login).  
**Проверка:** токен старше TTL → 401.

---

## Идеи будущего развития

Краткие продуктовые идеи без новых ID требований (не входят в Baseline).

- **Условный restart после return:** возвращать согласование с первого этапа только при изменении **значимых** полей; если изменены только второстепенные поля — продолжать с того же этапа, на котором был return (компромисс между OQ-A и текущим OQ-B).


---

## Карта ID (Baseline / backlog)

Полная карта всех ID требований по итогам этапа 3.

| ID | Bucket | Причина |
| :--- | :--- | :--- |
| UC-01 | Target-active | Login/JWT — Delivered; Legacy multi-role / ЛК в теле |
| UC-02 | backlog | Профиль / ЛК — Vision §7.1 |
| UC-03 | Baseline | Vision §8: каталог |
| UC-04 | Baseline | Vision §8: создание и отправка |
| UC-05 | Baseline | Vision §8: создание/отправка; доработка и повторная отправка |
| UC-06 | Baseline | Vision §8: мои заявки и карточка |
| UC-07 | Baseline | Vision §8: решения согласующего |
| UC-08 | Baseline | Vision §8: решения согласующего |
| UC-09 | Baseline | Vision §8: решения согласующего; доработка |
| UC-10 | Baseline | Vision §8: отмена |
| UC-11 | backlog | Админ-настройка типов — Vision §7.1 |
| UC-12 | backlog | Админ-настройка маршрутов — Vision §7.1 |
| UC-13 | Target-active | List notifications Delivered; mark-as-read (FR-NOTIF-03) — backlog |
| UC-14 | Baseline | История на карточке заявки (ядро) |
| UC-15 | backlog | Админ-реестр — Vision §7.1 |
| FR-ADMIN-01 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-02 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-03 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-04 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-05 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-06 | backlog | Админ-панель — Vision §7.1 |
| FR-ADMIN-07 | backlog | Админ-реестр — Vision §7.1 |
| FR-ADMIN-08 | backlog | Админ-история — Vision §7.1 |
| FR-APP-01 | Baseline | Очередь согласующего — Vision §8 |
| FR-APP-02 | Baseline | Карточка для approver — Vision §8 |
| FR-APP-03 | Baseline | Approve — Vision §8 |
| FR-APP-04 | Baseline | Reject — Vision §8 |
| FR-APP-05 | Baseline | Return — Vision §8 |
| FR-APP-06 | Baseline | Переход этапа — ядро |
| FR-APP-07 | Baseline | Завершение маршрута — ядро |
| FR-AUDIT-01 | Baseline | История на карточке — ядро |
| FR-AUDIT-02 | Baseline | Фиксация событий истории — ядро |
| FR-AUTH-01 | Target-active | JWT/логин — Delivered; Legacy wording |
| FR-AUTH-02 | Target-active | GET /me — Delivered; Legacy «роли» |
| FR-AUTH-03 | Target-active | AuthZ + role_id — Delivered; Legacy union |
| FR-CAB-01 | backlog | Профиль — Vision §7.1 |
| FR-CAB-02 | Baseline | Список «Мои заявки» — Vision §8 |
| FR-CAB-03 | backlog | Уведомления в кабинете — Vision §7.1 |
| FR-CAT-01 | Baseline | Каталог — Vision §8 |
| FR-CAT-02 | Baseline | Каталог — Vision §8 |
| FR-CAT-03 | Baseline | Каталог / форма — Vision §8 |
| FR-NOTIF-01 | Target-active | Создание in-app — Delivered |
| FR-NOTIF-02 | Target-active | GET /notifications — Delivered |
| FR-NOTIF-03 | backlog | Mark as read — не Target contract |
| FR-REQ-01 | Baseline | Создание — Vision §8 |
| FR-REQ-02 | Baseline | Заполнение / доработка — Vision §8 |
| FR-REQ-03 | Baseline | Отправка — Vision §8 |
| FR-REQ-04 | Baseline | Карточка — Vision §8 |
| FR-REQ-05 | Baseline | Статус на карточке — Vision §8 |
| FR-REQ-06 | Baseline | Комментарии на карточке — Vision §6 |
| FR-REQ-07 | Baseline | Отмена — Vision §8 |
| FR-REQ-08 | Baseline | Return на стороне заявки — Vision §8 |
| FR-REQ-09 | Baseline | Повторная отправка — Vision §8 |
| BR-01 | Baseline | Видимость employee — ядро |
| BR-02 | Baseline | Последовательный маршрут — Vision §12 |
| BR-03 | Baseline | First-approve wins — Vision §12 |
| BR-04 | Baseline | Reject — ядро |
| BR-05 | Baseline | Return — ядро |
| BR-06 | Baseline | Resubmit с этапа — Vision §12 |
| BR-07 | Baseline | Отмена draft/returned — Vision §12 |
| BR-08 | Baseline | Submit читает live-маршрут (без RouteInstance) — ADR-LIVE-CFG-01 |
| BR-09 | Baseline | Live config guard / in-flight caveat — ADR-LIVE-CFG-01 |
| BR-10 | Baseline | Каталог активных типов — ядро |
| BR-11 | Target-active | Уведомления — Target |
| BR-12 | Baseline | Нет auto-routing — Vision §7 |
| BR-13 | backlog | Реестр admin — Vision §7.1 |
| BR-14 | Baseline | Видимость approver — ядро |
| BR-15 | Baseline | Действие по своей задаче — ядро |
| BR-16 | Target | Одна роль на User (`role_id`); Legacy multi-role union — Previous |
| BR-17 | Baseline | Финальный approve — ядро |
| BR-18 | Baseline | Валидация маршрута при submit — ядро |
| BR-19 | Baseline | Создание draft — ядро |
| BR-20 | Baseline | Submit → in_approval — ядро |
| BR-21 | Baseline | Запрет самосогласования — ядро |
| BR-22 | Baseline | Resubmit с первого live-этапа — ядро |
| BR-23 | Target-active | События уведомлений — Target |
| BR-24 | Baseline | История на карточке — ядро |
| BR-25 | Baseline | Комментарий reject/return — ядро |
| BR-26 | Baseline | Live schema + working values — ядро |
| BR-27 | backlog | Правило admin — Vision §7.1 |
| BR-28 | Baseline | Свободные комментарии на карточке — ядро |
| BR-29 | Target-active | Атомарность уведомлений — Target |
| AC-ACC-01 | Baseline | Доступ employee — ядро |
| AC-ACC-02 | Baseline | Доступ approver — ядро |
| AC-ACC-03 | Baseline | Самосогласование — ядро |
| AC-ACC-04 | backlog | Админка — Vision §7.1 |
| AC-ACC-05 | backlog | Реестр admin — Vision §7.1 |
| AC-ACC-06 | Baseline | Полная карточка approver — ядро |
| AC-ADMIN-01 | backlog | Активация типа admin — Vision §7.1 |
| AC-APP-01 | Baseline | Создание draft — ядро |
| AC-APP-02 | Baseline | Submit — ядро |
| AC-APP-02b | Baseline | Submit при плохом маршруте — ядро |
| AC-APP-03 | Baseline | Задачи после submit — ядро |
| AC-APP-04 | Baseline | Approve — ядро |
| AC-APP-04b | Baseline | Approve с комментарием — ядро |
| AC-APP-05 | Baseline | Следующий этап — ядро |
| AC-APP-05b | Baseline | Завершение маршрута — ядро |
| AC-APP-06 | Baseline | Reject — ядро |
| AC-APP-06b | Baseline | Reject без комментария — ядро |
| AC-APP-07 | Baseline | Return — ядро |
| AC-APP-07b | Baseline | Return без комментария — ядро |
| AC-APP-08 | Baseline | Resubmit — ядро |
| AC-APP-09 | Baseline | First-approve wins — ядро |
| AC-APP-10 | Baseline | Live config in-flight caveat — ядро |
| AC-APP-10b | Baseline | Новый submit / новая конфигурация — ядро |
| AC-AUTH-01 | Target-active | Login Delivered; multi-role AC body — Legacy |
| AC-CAT-01 | Baseline | Неактивный тип — ядро |
| AC-CAT-01b | Baseline | Живые заявки после деактивации — ядро |
| AC-CAT-02 | Baseline | Пустой каталог — ядро |
| AC-DRAFT-01 | Baseline | Актуальная схема при edit — ядро |
| AC-DRAFT-02 | Baseline | Working RequestFieldValue / live schema — ядро (snapshot wording deprecated) |
| AC-NOTIF-01 | Target-active | TX уведомления — Delivered |
| AC-REQ-06 | Baseline | Комментарий на карточке — ядро |
| AC-REQ-07 | Baseline | Отмена — ядро |
| NFR-AVL-01 | Baseline | Режим поставки — ядро |
| NFR-AVL-02 | Baseline | Восстановление после рестарта — ядро |
| NFR-DEP-01 | Baseline | Python + Neon/local PG локально; Render + Neon в облаке |
| NFR-DEP-02 | Baseline | Seed-данные — Vision §9 |
| NFR-DEP-03 | Baseline | Конфигурация через env — ядро |
| NFR-LOG-01 | Baseline | Технические логи — ядро |
| NFR-LOG-02 | Baseline | Прикладная история заявки — ядро |
| NFR-LOG-03 | Baseline | Retention — ядро |
| NFR-MNT-01 | Baseline | OpenAPI — Vision §11 |
| NFR-MNT-02 | Baseline | Миграции БД — ядро |
| NFR-MNT-03 | Baseline | Трассируемые ID — ядро |
| NFR-PERF-01 | Baseline | Производительность чтения — ядро |
| NFR-PERF-02 | Baseline | Производительность записи — ядро |
| NFR-PERF-03 | Baseline | Пагинация — ядро |
| NFR-PERF-04 | Baseline | Baseline объёма — ядро |
| NFR-REL-01 | Baseline | Целостность статусов + история — ядро |
| NFR-REL-02 | Baseline | Идемпотентность — ядро |
| NFR-REL-03 | Baseline | Согласованность stage_id — ядро (snapshot wording deprecated) |
| NFR-SCL-01 | backlog | Multi-instance вне MVP — отложено |
| NFR-SCL-02 | Baseline | Рост числа типов — ядро |
| NFR-SEC-01 | Target-active | JWT-аутентификация — ADR-AUTH-JWT-01 |
| NFR-SEC-02 | Baseline | Авторизация ролей/владения — ядро |
| NFR-SEC-03 | Target-active | Хранение паролей — ADR-AUTH-JWT-01 |
| NFR-SEC-04 | Target-active | TTL токена — ADR-AUTH-JWT-01 |
| NFR-SEC-05 | Baseline | Скрытие чужих ресурсов — ядро |
| NFR-SEC-06 | Baseline | HTTPS внешнего стенда — ядро |
| NFR-USB-01 | Baseline | Понятность статусов — ядро |
| NFR-USB-02 | Baseline | Сообщения об ошибках — ядро |
| NFR-USB-03 | Baseline | Русский UI — ядро |

**Всего ID:** 143 (инвентарь: UC 15 + FR 38 + BR 29 + AC 32 + NFR 29 = 143).
