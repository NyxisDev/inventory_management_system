# ТЗ для DeepSeek: учёт товаров (Vue 3 + Quasar + FastAPI)

Last updated: 2026-11-07

## Как пользоваться

Отправляй части в DeepSeek строго по порядку: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. Каждый промпт лежит в отдельном блоке — копируй его целиком.

1. Часть 0 — первым сообщением в новом чате. Это контекст, без него DeepSeek будет придумывать своё.
2. Дальше по одной части за сообщение. Не переходи к следующей, пока код предыдущей не запустился (под каждой частью есть строка «Проверь»).
3. Если ответ обрезался — напиши «продолжи с того места, где остановился».
4. Если чат стал очень длинным — открой новый, вставь Часть 0 и файлы, которые уже есть (модели, список эндпоинтов), и потом следующую часть.

Что уже решено: роли admin и staff, PostgreSQL, несколько складов. Покупатель на сайте видит цену, фото, описание, точный остаток по складам, категории и поиск. Интерфейс админки и сайта — на английском. Пароли хранятся только как хэш — это обязательно для безопасности, сам пароль в базе не лежит.

## Часть 0 — общий контекст

Отправь первым сообщением. DeepSeek должен только ответить «понял», без кода.

```text
Ты — опытный fullstack-разработчик. Мы пишем проект по частям. Сейчас я даю общий контекст, потом буду присылать задачи по одной. Не пиши код, пока я не пришлю задачу. Сейчас коротко ответь, что понял, и задай вопросы, если что-то неясно.

ПРОЕКТ: система учёта товаров для магазина с несколькими складами + публичный сайт-каталог для покупателей.

СТРУКТУРА (один репозиторий):
/backend    — Python 3.12, FastAPI, SQLAlchemy 2.0 (async + asyncpg), Alembic, Pydantic v2, PostgreSQL 16
/admin-app  — Vue 3 + Quasar 2 (Vite, Composition API, <script setup>, Pinia, Vue Router, Axios) — приложение учёта для сотрудников
/shop-site  — Vue 3 + Quasar 2 — публичный сайт с ассортиментом (без регистрации, без корзины)
/docker-compose.yml — postgres, backend, admin-app, shop-site, nginx

РОЛИ:
- admin — всё: сотрудники, склады, категории, товары, остатки, журнал действий
- staff — товары, категории, приход / расход / перемещение / инвентаризация; НЕ управляет сотрудниками, НЕ видит журнал, НЕ создаёт склады
- покупатель (без входа) — только читает опубликованные товары: цена, фото, описание, категория, точный остаток по каждому складу

ОБЩИЕ ПРАВИЛА:
- Пароли хранить ТОЛЬКО как хэш (bcrypt), никогда открытым текстом и никогда не отдавать в API
- Авторизация: короткий JWT access token (15 минут) в заголовке Authorization: Bearer + refresh token в httpOnly cookie (подробно — в блоке БЕЗОПАСНОСТЬ)
- Все API под префиксом /api/v1; публичные (без входа) — /api/v1/public/...
- Деньги — Decimal / NUMERIC(12,2), никогда float
- Количество — NUMERIC(14,3), потому что есть единицы кг, м, м², м³, л
- Остаток никогда не меняется напрямую — только через операции склада, каждая пишется в историю движений
- Каждое действие сотрудника (создание, изменение, удаление, вход) пишется в журнал audit_log
- Настройки — через .env (pydantic-settings), пример в .env.example; секреты в код не зашивать
- Язык интерфейса — АНГЛИЙСКИЙ (и админка, и сайт, и тексты ошибок API). Все надписи UI вынести в vue-i18n (файл en.js), чтобы потом легко добавить другие языки. Названия на русском в моих задачах — это описание для тебя, в интерфейсе пиши их по-английски. Код, переменные и комментарии — тоже на английском

БЕЗОПАСНОСТЬ (обязательно в КАЖДОЙ задаче; если удобство противоречит безопасности — выбирай безопасность и скажи мне):
- Пароли: bcrypt (cost 12) или argon2id; минимум 10 символов, хотя бы одна буква и одна цифра
- Вход: одинаковое сообщение об ошибке и примерно одинаковое время ответа (проверять хэш даже если логина нет — защита от перебора логинов)
- Блокировка: 5 неудачных попыток — блок на 15 минут и по IP, и по логину (поля failed_login_attempts, locked_until)
- Access token (JWT HS256, 15 мин): секрет минимум 32 байта из .env; приложение не стартует, если JWT_SECRET пустой, короткий или дефолтный; проверять exp; в токене только id и role
- Refresh token: случайная строка (secrets.token_urlsafe(48)), в БД хранится только SHA-256 хэш (таблица refresh_tokens), cookie httpOnly + Secure + SameSite=Strict + path=/api/v1/auth, срок 7 дней, ротация при каждом обновлении; повторное использование старого токена = отзыв всех токенов сотрудника
- При деактивации сотрудника, смене или сбросе пароля — отзывать все его refresh токены
- На фронтенде access token хранится ТОЛЬКО в памяти (Pinia), не в localStorage; автовыход админки после 30 минут бездействия
- Права проверяются на бэкенде в КАЖДОМ эндпоинте; фронтенд только прячет кнопки. Проверять, что объект существует и доступен (защита от IDOR)
- SQL: только ORM и параметры, никакой склейки строк; поле сортировки — только из белого списка
- Все входные данные — через Pydantic: длины строк, диапазоны чисел, model_config extra='forbid'
- XSS: HTML описания чистить bleach на бэкенде и DOMPurify на фронтенде; v-html нигде, кроме описания товара
- Файлы: проверять реальный тип через Pillow, перекодировать (это удаляет EXIF и вредное содержимое), имя — uuid, путь никогда не строится из ввода пользователя, лимит размера и в nginx, и в бэкенде; в папке media ничего не исполняется
- Заголовки (nginx): Content-Security-Policy, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy, HSTS на проде
- CORS: только конкретные домены из .env, никогда "*" вместе с credentials
- Rate limit (slowapi): login и refresh — строго; публичное API — около 120 запросов в минуту на IP
- Прод: DEBUG выключен; /docs и /openapi.json выключены (ENABLE_DOCS=false); наружу ошибки без стектрейсов, подробности — только в серверный лог
- Никогда не писать пароли, хэши и токены в логи сервера и в audit_log
- БД: приложение подключается отдельным пользователем без прав суперпользователя; порт БД наружу не открыт
- Docker: контейнеры работают не от root; .env в .gitignore, в репозитории только .env.example
- Зависимости с зафиксированными версиями; pip-audit и npm audit не должны показывать критичных уязвимостей
- Админка закрыта от поисковиков (X-Robots-Tag: noindex и robots.txt)

КАК ОТВЕЧАТЬ НА ЗАДАЧИ:
- Пиши полный код каждого файла, без "..." и "остальное аналогично"
- Перед каждым файлом пиши его путь, например: // backend/app/main.py
- В конце — команды для запуска и проверки
- Если ответ получается очень длинным — разбей на порции и скажи мне написать "продолжи"
- Не меняй стек и схему БД без моего согласия
```

## Часть 1 — база данных

В базе 9 таблиц: твои четыре (сотрудники, товары, количество, логи) плюс то, что нужно для складов, категорий и фото.

| Таблица | Что хранит |
| --- | --- |
| employees | Имя, фамилия, логин, хэш пароля, роль (admin/staff), активен ли, блокировка после неудачных входов. Сессии входа — в отдельной таблице refresh\_tokens |
| categories | Категории товаров, можно вложенные |
| warehouses | Склады / магазины и их адреса |
| products | Товар: артикул, название, описание, цена, единица, опубликован ли |
| product\_images | Фото товара, одно главное |
| stock | Сколько товара на каждом складе сейчас |
| stock\_movements | История: кто, когда, сколько принёс / списал / переместил |
| audit\_log | Логи: какой сотрудник что сделал, что было и что стало |

```text
ЗАДАЧА 1 — БАЗА ДАННЫХ (backend).

Ниже готовая схема PostgreSQL. Не меняй её без спроса. Сделай по ней:
1) backend/app/core/config.py — Settings (pydantic-settings): DATABASE_URL, JWT_SECRET, JWT_EXPIRE_MINUTES, ADMIN_USERNAME, ADMIN_PASSWORD, MEDIA_DIR, CORS_ORIGINS, ENABLE_DOCS, TRUST_PROXY, COOKIE_SECURE, REFRESH_EXPIRE_DAYS
2) backend/app/db.py — async engine, async_sessionmaker, зависимость get_session для FastAPI
3) backend/app/models/ — модели SQLAlchemy 2.0 (Mapped, mapped_column) на каждую таблицу, с relationship и Enum-типами
4) Alembic (async-шаблон) и первая миграция, которая создаёт ВСЁ ниже: расширение, enum-типы, CHECK, индексы, триггеры (через op.execute)
5) backend/app/seed.py — скрипт (python -m app.seed): создаёт первого админа из ADMIN_USERNAME / ADMIN_PASSWORD, склад "Main warehouse" и 2 категории; повторный запуск не создаёт дубли
6) backend/requirements.txt (с зафиксированными версиями) и backend/.env.example
7) backend/db/init_roles.sql: два пользователя PostgreSQL — app_owner (владелец таблиц, под ним идут миграции) и app_user (под ним работает приложение, без SUPERUSER и без CREATE). app_user получает SELECT/INSERT/UPDATE/DELETE на таблицы, но на audit_log — ТОЛЬКО SELECT и INSERT. В .env два разных URL: DATABASE_URL (app_user) и MIGRATIONS_DATABASE_URL (app_owner)

СХЕМА:

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE employee_role AS ENUM ('admin', 'staff');
CREATE TYPE movement_type AS ENUM ('income', 'outcome', 'adjustment', 'transfer_in', 'transfer_out');
CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'login', 'login_failed', 'logout', 'stock_change');

CREATE TABLE employees (
  id            SERIAL PRIMARY KEY,
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          employee_role NOT NULL DEFAULT 'staff',
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  failed_login_attempts INT NOT NULL DEFAULT 0,
  locked_until  TIMESTAMPTZ,                 -- временная блокировка после 5 ошибок
  password_changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login_at TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE refresh_tokens (
  id          BIGSERIAL PRIMARY KEY,
  employee_id INT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  token_hash  CHAR(64) NOT NULL UNIQUE,      -- SHA-256 от токена, сам токен не хранится
  expires_at  TIMESTAMPTZ NOT NULL,
  revoked_at  TIMESTAMPTZ,
  replaced_by BIGINT REFERENCES refresh_tokens(id),
  ip_address  INET,
  user_agent  VARCHAR(500),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_employee ON refresh_tokens(employee_id);

CREATE TABLE categories (
  id         SERIAL PRIMARY KEY,
  name       VARCHAR(150) NOT NULL,
  slug       VARCHAR(150) NOT NULL UNIQUE,
  parent_id  INT REFERENCES categories(id) ON DELETE SET NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE warehouses (
  id           SERIAL PRIMARY KEY,
  name         VARCHAR(150) NOT NULL UNIQUE,
  address      VARCHAR(255),
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  show_on_site BOOLEAN NOT NULL DEFAULT TRUE,   -- показывать ли остаток этого склада покупателям
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
  id           SERIAL PRIMARY KEY,
  sku          VARCHAR(64)  NOT NULL UNIQUE,      -- артикул
  name         VARCHAR(255) NOT NULL,
  slug         VARCHAR(255) NOT NULL UNIQUE,      -- для адреса на сайте: /product/<slug>
  description  TEXT,                             -- HTML из редактора
  category_id  INT REFERENCES categories(id) ON DELETE SET NULL,
  unit         VARCHAR(16)  NOT NULL DEFAULT 'pcs', -- pcs, kg, m, m², m³, l, pack
  price        NUMERIC(12,2) NOT NULL CHECK (price >= 0),
  is_published BOOLEAN NOT NULL DEFAULT FALSE,     -- виден ли на сайте
  is_archived  BOOLEAN NOT NULL DEFAULT FALSE,     -- вместо удаления
  created_by   INT REFERENCES employees(id) ON DELETE SET NULL,
  updated_by   INT REFERENCES employees(id) ON DELETE SET NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_products_category  ON products(category_id);
CREATE INDEX ix_products_name_trgm ON products USING gin (name gin_trgm_ops);
CREATE INDEX ix_products_sku_trgm  ON products USING gin (sku gin_trgm_ops);

CREATE TABLE product_images (
  id         SERIAL PRIMARY KEY,
  product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  file_path  VARCHAR(500) NOT NULL,
  is_main    BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_product_images_main ON product_images(product_id) WHERE is_main;

CREATE TABLE stock (
  product_id   INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
  quantity     NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
  min_quantity NUMERIC(14,3) NOT NULL DEFAULT 0,  -- ниже этого = "мало на складе"
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (product_id, warehouse_id)
);

CREATE TABLE stock_movements (
  id              BIGSERIAL PRIMARY KEY,
  product_id      INT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  warehouse_id    INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
  employee_id     INT REFERENCES employees(id) ON DELETE SET NULL,
  type            movement_type NOT NULL,
  quantity_change NUMERIC(14,3) NOT NULL,   -- плюс = пришло, минус = ушло
  quantity_after  NUMERIC(14,3) NOT NULL,   -- остаток после операции
  transfer_group  UUID,                     -- связывает пару transfer_out + transfer_in
  comment         VARCHAR(500),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_movements_product   ON stock_movements(product_id, created_at DESC);
CREATE INDEX ix_movements_warehouse ON stock_movements(warehouse_id, created_at DESC);
CREATE INDEX ix_movements_employee  ON stock_movements(employee_id, created_at DESC);

CREATE TABLE audit_log (
  id            BIGSERIAL PRIMARY KEY,
  employee_id   INT REFERENCES employees(id) ON DELETE SET NULL,
  employee_name VARCHAR(201),               -- "Имя Фамилия" на момент действия
  action        audit_action NOT NULL,
  entity_type   VARCHAR(50) NOT NULL,       -- product, employee, category, warehouse, stock, product_image, auth
  entity_id     VARCHAR(64),
  old_data      JSONB,
  new_data      JSONB,
  ip_address    INET,
  user_agent    VARCHAR(500),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_employee ON audit_log(employee_id, created_at DESC);
CREATE INDEX ix_audit_entity   ON audit_log(entity_type, entity_id);
CREATE INDEX ix_audit_created  ON audit_log(created_at DESC);

-- автообновление updated_at
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_employees_upd  BEFORE UPDATE ON employees  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_categories_upd BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_warehouses_upd BEFORE UPDATE ON warehouses FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_products_upd   BEFORE UPDATE ON products   FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_stock_upd      BEFORE UPDATE ON stock      FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- журнал нельзя изменить или удалить
CREATE OR REPLACE FUNCTION forbid_audit_change() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_audit_readonly BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION forbid_audit_change();
```

Проверь: `alembic upgrade head` проходит без ошибок, `python -m app.seed` создаёт админа, в таблице employees в поле password\_hash лежит строка вида `$2b$12$...`, а не сам пароль.

## Часть 2 — бэкенд FastAPI

Это самая большая часть. Если DeepSeek обрежет ответ, попроси сначала пункты 1–3, потом 4–8.

```text
ЗАДАЧА 2 — БЭКЕНД FastAPI (на основе моделей из задачи 1).

СТРУКТУРА:
backend/app/main.py
backend/app/core/security.py        — хэш паролей (passlib[bcrypt]), создание/проверка JWT (python-jose или PyJWT)
backend/app/api/deps.py             — get_current_employee, require_admin
backend/app/api/v1/routers/         — auth, employees, categories, warehouses, products, images, stock, public
backend/app/schemas/                — Pydantic v2: отдельно Create / Update / Read для каждой сущности
backend/app/services/               — бизнес-логика (роутеры тонкие, логика в сервисах)

1) АВТОРИЗАЦИЯ
- POST /api/v1/auth/login {username, password} → {access_token, token_type, employee: {id, first_name, last_name, role}} + ставит refresh cookie
- POST /api/v1/auth/refresh — по refresh cookie выдаёт новый access token и НОВЫЙ refresh (старый отзывается); обязателен заголовок X-Requested-With: XMLHttpRequest (защита от CSRF); если пришёл уже отозванный токен — отозвать ВСЕ сессии сотрудника (признак кражи)
- POST /api/v1/auth/logout — отзывает текущий refresh и удаляет cookie; POST /api/v1/auth/logout-all — выход со всех устройств
- access token, выпущенный раньше password_changed_at, считается недействительным
- Неверный логин или пароль → 401 с одним и тем же текстом "Invalid username or password" (не подсказывать, что именно неверно)
- Неактивный сотрудник → 403
- 5 неудачных попыток для одного логина → locked_until = now + 15 мин (счётчик в БД, сбрасывается при успехе); по IP — лимит slowapi → 429. Сообщение при блокировке не раскрывает, существует ли логин
- При успешном входе обновлять last_login_at
- GET  /api/v1/auth/me
- POST /api/v1/auth/change-password {old_password, new_password} — новый пароль по правилам из БЕЗОПАСНОСТЬ (минимум 10 символов, буква и цифра), не равен старому; после смены — обновить password_changed_at и отозвать все другие сессии
- В JWT: sub = id сотрудника, role. На каждом запросе проверять, что сотрудник ещё is_active

2) СОТРУДНИКИ (только admin)
- GET /api/v1/employees — поиск по имени/фамилии/логину, фильтр role/is_active, пагинация
- POST /api/v1/employees {first_name, last_name, username, password, role}
- PATCH /api/v1/employees/{id} — имя, фамилия, роль, is_active
- POST /api/v1/employees/{id}/reset-password {new_password}
- DELETE нет — только деактивация (is_active=false)
- Нельзя деактивировать или понизить самого себя и последнего активного админа → 409
- password_hash никогда не попадает в ответы

3) КАТЕГОРИИ (чтение и запись — staff и admin)
- GET /api/v1/categories (плоский список) и GET /api/v1/categories/tree (дерево)
- POST, PATCH, DELETE; slug генерировать из названия (python-slugify, кириллица транслитерируется), при совпадении добавлять -2, -3
- Нельзя удалить категорию, если в ней есть товары или подкатегории → 409

4) СКЛАДЫ
- GET /api/v1/warehouses — staff и admin
- POST, PATCH — только admin; удаление нельзя, только is_active=false

5) ТОВАРЫ (staff и admin)
- GET /api/v1/products — фильтры: q (поиск по названию и артикулу, ILIKE + pg_trgm), category_id, warehouse_id, is_published, is_archived (по умолчанию false), low_stock=true (где quantity <= min_quantity хотя бы на одном складе); сортировка sort=name|price|created_at|-price и т.д.; пагинация page, page_size (макс 100); ответ {items, total, page, page_size}
- В списке у каждого товара: главное фото, total_quantity (сумма по складам), is_low_stock
- GET /api/v1/products/{id} — всё + остатки по каждому складу + все фото
- POST, PATCH /api/v1/products/{id} — slug генерировать автоматически; created_by / updated_by = текущий сотрудник
- description — HTML: перед сохранением чистить через bleach (разрешить p, br, b, strong, i, em, ul, ol, li, h3, h4, a[href])
- DELETE /api/v1/products/{id} — если у товара есть движения по складу, не удалять, а ставить is_archived=true и is_published=false; если движений нет — удалять

6) ФОТО ТОВАРА
- POST /api/v1/products/{id}/images — multipart, можно несколько файлов; только jpg/png/webp, до 5 МБ каждый
- Реальный тип файла проверять через Pillow (не по расширению); уменьшать до 1600px по длинной стороне, сохранять в webp; плюс миниатюра 400px
- Имя файла — uuid4; папка MEDIA_DIR/products/{product_id}/
- Первое фото автоматически становится главным
- PATCH /api/v1/products/{id}/images/{image_id} {is_main, sort_order}; DELETE — удаляет и файл
- Раздавать /media через StaticFiles

7) СКЛАД (staff и admin)
- GET  /api/v1/stock?product_id=&warehouse_id=
- POST /api/v1/stock/income     {product_id, warehouse_id, quantity > 0, comment?}
- POST /api/v1/stock/outcome    {product_id, warehouse_id, quantity > 0, comment?} — если остатка не хватает → 409 "Not enough stock in this warehouse"
- POST /api/v1/stock/adjustment {product_id, warehouse_id, new_quantity >= 0, comment обязателен} — инвентаризация, в движение пишется разница
- POST /api/v1/stock/transfer   {product_id, from_warehouse_id, to_warehouse_id, quantity > 0, comment?} — два движения transfer_out и transfer_in с одним transfer_group (uuid4)
- PATCH /api/v1/stock/min-quantity {product_id, warehouse_id, min_quantity}
- GET /api/v1/stock/movements — фильтры product_id, warehouse_id, employee_id, type, date_from, date_to; пагинация; новые сверху; в ответе имя товара, склада и сотрудника
- КАЖДАЯ операция — в одной транзакции; строку stock блокировать SELECT ... FOR UPDATE; если строки нет — создать с 0; в stock_movements писать quantity_change и quantity_after
- Нельзя делать операции с архивным товаром или неактивным складом → 409

8) ПУБЛИЧНОЕ API (без авторизации, только чтение)
- GET /api/v1/public/categories — дерево, только категории, где есть опубликованные товары
- GET /api/v1/public/products — только is_published=true и is_archived=false; фильтры q, category_slug (включая подкатегории), price_min, price_max, in_stock=true; сортировка price, -price, name, -created_at; пагинация
- GET /api/v1/public/products/{slug} — name, sku, description, price, unit, category, images, stock: [{warehouse_name, address, quantity}] только по складам is_active и show_on_site, total_quantity
- НЕ отдавать служебные поля: created_by, updated_by, min_quantity, is_archived, id сотрудников
- Кэш-заголовок Cache-Control: public, max-age=60

ОБЩЕЕ:
- CORS из настроек CORS_ORIGINS (адреса admin-app и shop-site)
- Единый формат ошибок {"detail": "text in English"}
- GET /api/v1/health → {"status": "ok"}
- Swagger на /docs
- В сервисах оставь места (функцию-заглушку log_action), куда в задаче 3 добавим запись в журнал
- Тесты pytest + httpx.AsyncClient (отдельная тестовая БД): вход админа; staff создаёт товар; staff получает 403 на /employees; расход больше остатка → 409; перемещение меняет остатки на обоих складах
```

Проверь: в Swagger (`http://localhost:8000/docs`) можно войти админом, создать склад, товар, сделать приход и увидеть товар в `/api/v1/public/products` после того, как поставишь is\_published.

## Часть 3 — логи действий сотрудников

Лог пишется в той же транзакции, что и само изменение: если действие не прошло, лишней записи не будет. Записи сохраняют и «было», и «стало», а удалить их нельзя даже напрямую в базе.

```text
ЗАДАЧА 3 — ЖУРНАЛ ДЕЙСТВИЙ (audit_log). Таблица уже есть из задачи 1.

1) backend/app/services/audit.py:
   async def log_action(session, *, employee, action, entity_type, entity_id=None, old_data=None, new_data=None, request=None)
   - добавляет запись в ТУ ЖЕ сессию/транзакцию, что и изменение (сама не делает commit)
   - employee_name = "Имя Фамилия" на момент действия
   - ip_address: из X-Forwarded-For только если включена настройка TRUST_PROXY, иначе request.client.host; user_agent — из заголовка (обрезать до 500)
   - Decimal, datetime, UUID сериализовать в строки для JSONB

2) ЧТО ЗАПИСЫВАТЬ в old_data / new_data:
   - create → old_data = null, new_data = полный объект
   - update → ТОЛЬКО изменившиеся поля: old_data = {"price": "100.00"}, new_data = {"price": "120.00"}; если ничего не изменилось — запись не создавать
   - delete → old_data = полный объект, new_data = null
   - НИКОГДА не писать password, password_hash, токены — заменять на "***" (сделай функцию mask_sensitive)
   - Для длинного description сохранять текст целиком (это нужно, чтобы восстановить описание)

3) КАКИЕ ДЕЙСТВИЯ ЛОГИРОВАТЬ (встроить вызовы во все сервисы из задачи 2):
   - auth: login (успех), login_failed (employee_id = null, new_data = {"username": "..."}), logout, смена и сброс пароля (без самого пароля!)
   - create / update / delete для: employee, category, warehouse, product, product_image
   - архивация товара = update с {"is_archived": false} → {"is_archived": true}
   - stock_change для каждой складской операции: entity_type = "stock", entity_id = "{product_id}:{warehouse_id}",
     old_data = {"quantity": было}, new_data = {"quantity": стало, "type": "income", "change": "+5", "movement_id": ..., "comment": ...}
   - для перемещения — две записи (склад-отправитель и склад-получатель)

4) API ЖУРНАЛА (только admin):
   - GET /api/v1/audit — фильтры employee_id, action, entity_type, entity_id, date_from, date_to, q (поиск по employee_name); пагинация; новые сверху
   - В каждой записи отдавать готовое поле changes: [{field, old, new}] — чтобы фронтенд просто показал таблицу
   - И человеческое описание summary на английском, например: "John Smith changed the price of «Cement M500»: 100.00 → 120.00"
   - GET /api/v1/audit/export.csv — те же фильтры, CSV в UTF-8 с BOM (чтобы Excel открывал кириллицу), разделитель ";"
   - GET /api/v1/audit/entity/{entity_type}/{entity_id} — история одного объекта (для вкладки "История" в карточке товара)
   - PUT / PATCH / DELETE для журнала НЕ делать

5) ТЕСТЫ:
   - изменение цены товара создаёт запись с old_data {"price": "100.00"} и new_data {"price": "120.00"}
   - создание сотрудника: в журнале нет пароля и хэша
   - неудачный расход (409) не создаёт запись в журнале
   - staff получает 403 на GET /api/v1/audit
   - попытка UPDATE audit_log через SQL падает с ошибкой (триггер из задачи 1)
```

Проверь: поменяй цену товара в Swagger, потом открой `GET /api/v1/audit` — там должна быть запись с твоим именем, старой и новой ценой.

## Часть 4 — приложение учёта для сотрудников

Перед этой частью лучше вставить DeepSeek список эндпоинтов из Swagger (или файл `openapi.json` с адреса `/openapi.json`), чтобы фронтенд совпал с бэкендом. Эту часть тоже можно просить по кускам: сначала каркас и вход, потом страницы.

```text
ЗАДАЧА 4 — ПРИЛОЖЕНИЕ УЧЁТА ДЛЯ СОТРУДНИКОВ (/admin-app). Вот мой openapi.json: [вставлю сюда]

СТЕК: Quasar 2 + Vue 3, создать через `npm init quasar` (Quasar CLI with Vite, Composition API + <script setup>, Pinia, Axios, ESLint). Языковой пакет Quasar — en-US, все надписи на английском через vue-i18n. Плагины Quasar: Notify, Dialog, Loading.

КАРКАС:
- src/boot/axios.js — baseURL из import.meta.env.VITE_API_URL; withCredentials: true; заголовок X-Requested-With: XMLHttpRequest; interceptor добавляет Bearer-токен; на 401 — ОДИН раз вызвать /auth/refresh и повторить запрос (несколько одновременных запросов ждут один общий refresh), если не вышло — logout и переход на /login; ошибки показывать через Notify (текст из detail)
- src/api/ — отдельные модули: auth.js, employees.js, categories.js, warehouses.js, products.js, stock.js, audit.js
- src/stores/auth.js (Pinia) — access token ТОЛЬКО в памяти (НЕ в LocalStorage и не в sessionStorage), employee, геттер isAdmin, действия login / logout / refresh / fetchMe; при старте приложения вызывать /auth/refresh, чтобы восстановить сессию из cookie; автовыход после 30 минут бездействия; выход в одной вкладке завершает сессию во всех (BroadcastChannel)
- Роутер: meta.requiresAuth и meta.requiresAdmin, глобальный guard; staff, открывший админскую страницу, попадает на главную с уведомлением
- MainLayout: QHeader (название, имя и фамилия сотрудника, роль, меню: сменить пароль / выйти), QDrawer с меню; пункты «Сотрудники» и «Журнал» видны только admin
- Общие компоненты: ProductSelect (QSelect с поиском через API, показывает артикул и название), WarehouseSelect, CategorySelect, ConfirmDialog, PriceInput, QuantityInput (дробные числа, запятая или точка)

СТРАНИЦЫ:
1. /login — LoginPage: логин, пароль (с кнопкой показать), ошибка под формой
2. / — DashboardPage: карточки «Всего товаров», «Мало на складе», «Не опубликовано»; список товаров с низким остатком; последние 10 движений по складу
3. /products — ProductsPage: QTable с серверной пагинацией и сортировкой (@request); поиск с debounce 300 мс; фильтры: категория, склад, опубликован, архив, мало на складе; фильтры сохраняются в URL query
   Колонки: миниатюра фото, артикул, название, категория, цена, ед., общий остаток (красным, если мало), опубликован (QToggle прямо в таблице), действия (редактировать, в архив)
   На телефоне таблица превращается в карточки (grid mode)
4. /products/new и /products/:id — ProductFormPage, вкладки (QTabs):
   «Основное» — название, артикул, категория, единица (pcs, kg, m, m², m³, l, pack), цена, описание (QEditor), опубликован
   «Фото» — загрузка нескольких фото (QUploader или QFile + превью), выбор главного, удаление, смена порядка стрелками
   «Остатки» — таблица по складам (склад, количество, минимум — минимум редактируется) + кнопки «Приход», «Расход», «Переместить», открывают диалог с уже выбранным товаром
   «История» — движения по складу этого товара; для admin ещё журнал изменений товара (GET /audit/entity/product/{id})
   Предупреждение при уходе со страницы с несохранёнными изменениями
5. /stock — StockPage, вкладки «Приход» / «Расход» / «Перемещение» / «Инвентаризация»: товар (ProductSelect), склад, количество, комментарий; показывать текущий остаток и «будет после операции»; после успеха — Notify и очистка формы (склад остаётся выбранным)
6. /movements — MovementsPage: история движений с фильтрами (товар, склад, тип, сотрудник, период через QDate range); приход зелёным, расход красным
7. /categories — CategoriesPage: QTree + диалог создания/редактирования (название, родитель, порядок)
8. /warehouses — WarehousesPage: список; создать/редактировать/выключить — только admin; галочка «показывать на сайте»
9. /employees (admin) — EmployeesPage: таблица (имя, фамилия, логин, роль, активен, последний вход); диалог создания (имя, фамилия, логин, пароль + кнопка «сгенерировать», роль); редактирование; деактивация; сброс пароля
10. /audit (admin) — AuditPage: таблица (дата и время, сотрудник, действие, объект, summary); фильтры (сотрудник, действие, тип объекта, период); раскрывающаяся строка с таблицей «поле | было | стало» из changes, IP и браузер; кнопка «Выгрузить CSV»

ОБЩЕЕ:
- Работает на компьютере, планшете и телефоне
- Опасные действия (архив, деактивация, расход, удаление фото) — только через подтверждение
- Валидация всех форм (rules), состояния загрузки на кнопках и таблицах, пустые состояния («No products yet»)
- Деньги и количества форматировать через Intl.NumberFormat; даты — в локальном времени, формат dd.MM.yyyy HH:mm
- .env.example: VITE_API_URL=/api/v1; в quasar.config devServer.proxy перенаправляет /api на http://localhost:8000, чтобы cookie работали как на одном домене
- Никаких секретов в фронтенде (всё из VITE_* видно всем); в консоль не выводить токены; пароли в формах — autocomplete="current-password" / "new-password"
```

Проверь: войди админом, создай сотрудника staff, выйди и зайди под ним — пунктов «Сотрудники» и «Журнал» не должно быть, а приход товара должен работать.

## Часть 5 — сайт-каталог для покупателей

Сайт — отдельный Quasar-проект в режиме SSR, чтобы товары находились в Google. Он только читает публичное API и ничего не меняет.

```text
ЗАДАЧА 5 — ПУБЛИЧНЫЙ САЙТ-КАТАЛОГ (/shop-site).

СТЕК: отдельный проект Quasar 2 + Vue 3 (<script setup>, Pinia), режим SSR (quasar mode add ssr) для SEO. Данные грузить так, чтобы они были в HTML с сервера (preFetch или serverPrefetch + Pinia). Если SSR сильно усложняет — скажи мне до того, как писать код.
Использует ТОЛЬКО /api/v1/public/... Нет входа, корзины и заказов.
Настройки в .env: API_URL, SITE_NAME, SHOP_PHONE, SHOP_EMAIL, SHOP_ADDRESS, SHOP_HOURS (часы работы).

СТРАНИЦЫ:
1. / — главная: шапка (название магазина, поиск, телефон), категории плитками, блок «New arrivals» (8 последних товаров)
2. /catalog и /catalog/:categorySlug — каталог:
   - слева фильтры: дерево категорий, цена от–до (QRange + поля), «только в наличии»; на телефоне фильтры в выдвижной панели
   - сверху сортировка: сначала дешёвые, дорогие, по названию, новинки
   - сетка карточек: фото, название, цена «€120.00 / m²», «In stock: 12 m²» зелёным или «Out of stock» серым
   - пагинация; ВСЕ фильтры и страница — в URL query, чтобы ссылкой можно было поделиться
   - хлебные крошки (QBreadcrumbs)
3. /product/:slug — карточка товара:
   - галерея (QCarousel + миниатюры, увеличение по клику в диалоге)
   - название, артикул, цена за единицу, категория
   - описание (HTML) — перед v-html обязательно чистить DOMPurify (isomorphic-dompurify для SSR)
   - таблица «Availability by warehouse»: склад, адрес, количество + итого
   - блок «How to buy»: телефон (ссылка tel:), адрес, часы работы
   - «Similar products» — 4 товара из той же категории
4. /search?q= — результаты поиска; в шапке поиск с подсказками (первые 5 товаров, debounce 300 мс)
5. /contacts — контакты и список складов/магазинов с адресами
6. 404 — если товар или категория не найдены (и HTTP-статус 404 на сервере)

SEO:
- useMeta на каждой странице: title, description, og:title, og:image (главное фото), canonical
- на карточке товара — JSON-LD schema.org/Product (name, image, sku, offers: price, priceCurrency, availability)
- /sitemap.xml и /robots.txt (через SSR-middleware)

ДИЗАЙН:
- чистый, светлый, mobile-first; фирменный цвет через переменную $primary в quasar.variables.scss, чтобы легко поменять
- QSkeleton при загрузке, ленивая загрузка картинок (QImg), в каталоге — миниатюры 400px
- заглушка-картинка для товара без фото
- футер: контакты, часы работы, адрес
- валюта и формат цены — через настройку CURRENCY в .env (по умолчанию EUR)
```

Проверь: опубликуй товар в админке — он появляется на сайте; сними галочку — исчезает. Открой код страницы (Ctrl+U): название и цена товара должны быть в HTML.

## Часть 6 — запуск через Docker Compose

Одна команда `docker compose up -d` поднимает всё: базу, бэкенд, админку и сайт. Так же потом можно запустить на сервере (VPS).

```text
ЗАДАЧА 6 — ЗАПУСК И ДЕПЛОЙ.

1) docker-compose.yml в корне:
   - db: postgres:16, volume pgdata, healthcheck (pg_isready), порт наружу НЕ открывать
   - backend: Dockerfile на python:3.12-slim; перед стартом alembic upgrade head, потом uvicorn (2 воркера); volume media для фото; стартует после того, как db healthy
   - admin-app: многоэтапная сборка (node:20 → quasar build → nginx:alpine раздаёт dist/spa, с fallback на index.html)
   - shop-site: сборка quasar build -m ssr, запуск node dist/ssr/index.js
   - nginx: единая точка входа:
       shop.домен  → shop-site
       admin.домен → admin-app
       /api и /media на обоих доменах → backend
     для локального запуска — вариант на портах localhost:8080 (сайт) и localhost:8081 (админка)
     client_max_body_size 25m (для фото), кэш для /media на 7 дней, gzip
   - HTTPS: покажи как подключить Let's Encrypt (certbot или замена nginx на Caddy — предложи, что проще)

2) .env.example в корне со всеми переменными всех сервисов и комментарием к каждой; JWT_SECRET и пароль БД — с пометкой "ОБЯЗАТЕЛЬНО ЗАМЕНИТЬ" и командой для генерации (openssl rand -hex 32)

3) БЭКАПЫ:
   - сервис или скрипт backup.sh: ежедневно pg_dump в папку backups/ + архив папки media, хранить последние 14 дней
   - restore.sh — восстановление из бэкапа

4) Makefile или scripts/: up, down, logs, migrate, seed (создать первого админа), test, backup

5) README.md на русском:
   - что нужно установить
   - запуск для разработки без Docker (бекенд + два фронтенда с hot reload, только БД в Docker)
   - запуск через Docker и создание первого админа
   - деплой на VPS (Ubuntu 24.04) шаг за шагом, включая домен и HTTPS
   - как обновить проект (git pull + пересборка + миграции)
   - как сделать и восстановить бэкап
```

Проверь: на чистом компьютере с Docker по README проект запускается за несколько команд, а после `docker compose down` и `up` товары и фото не пропадают.

## Часть 7 — проверка безопасности

Правила безопасности уже есть в Части 0, и DeepSeek соблюдает их с первой задачи. Эта часть — финальная проверка: DeepSeek ищет дыры во всём готовом коде, исправляет их и пишет тесты, которые атакуют приложение. Перед отправкой вставь в чат актуальные файлы бэкенда.

```text
ЗАДАЧА 7 — АУДИТ БЕЗОПАСНОСТИ. Вот текущий код: [вставлю файлы]

Представь, что ты пентестер, который хочет взломать этот проект. Пройди по чек-листу (OWASP Top 10 + ASVS уровень 1) и для КАЖДОГО пункта ответь: "ок" / "проблема: где, чем опасно, исправление (код)".

ЧЕК-ЛИСТ:
1. Доступ: каждый эндпоинт проверяет авторизацию и роль; staff не может вызвать ни один admin-эндпоинт; нет IDOR (подмена id в URL и в теле запроса)
2. Аутентификация: подбор пароля, перебор логинов (одинаковые ответы и время), блокировка, ротация и отзыв refresh, отзыв сессий при деактивации и смене пароля, просроченный и поддельный JWT, alg=none
3. Инъекции: SQL (поиск q, sort, фильтры), заголовки, CSV injection в экспорте журнала (ячейки, начинающиеся с = + - @, экранировать)
4. XSS: описание товара, названия, комментарии, summary в журнале, поиск на сайте; CSP действительно работает
5. Загрузка файлов: файл .php или .svg с расширением .jpg, огромная картинка (decompression bomb — Image.MAX_IMAGE_PIXELS), path traversal в имени
6. CSRF: refresh и logout защищены (SameSite + X-Requested-With); CORS не пропускает чужие домены
7. Утечки: password_hash, токены и стектрейсы не попадают в ответы и логи; публичное API не отдаёт служебные поля; /docs закрыт на проде
8. Бизнес-логика: отрицательные количества и цены, огромные числа, гонка двух одновременных расходов (остаток не уходит в минус), перемещение на тот же склад, операции с архивным товаром
9. Журнал: нельзя изменить и удалить ни через API, ни пользователем app_user в БД; все важные действия логируются
10. Инфраструктура: заголовки безопасности в nginx, HTTPS и HSTS, контейнеры не от root, порт БД закрыт, секреты не в git, лимиты размера запросов
11. Зависимости: запусти мысленно pip-audit и npm audit, подскажи, какие версии обновить

ПОСЛЕ ЧЕК-ЛИСТА:
- дай исправленный код всех файлов, где были проблемы
- напиши backend/tests/test_security.py: staff → 403 на /employees и /audit; без токена → 401; просроченный и поддельный токен → 401; повторно использованный refresh → все сессии отозваны; 6-я неудачная попытка входа → блокировка; SQL-инъекция в q и sort не ломает запрос; <script> в описании вырезается; .php под видом .jpg → 400; два параллельных расхода не уводят остаток в минус; ответ /employees не содержит password_hash
- добавь в Makefile команду security-check: pytest tests/test_security.py + pip-audit + npm audit --audit-level=high
- в конце напиши, что ещё стоит сделать вручную перед запуском (например, проверить сайт сканером OWASP ZAP baseline)
```

Проверь: `make security-check` проходит без ошибок. Кроме того, раз в несколько месяцев снова запускай Часть 7 с актуальным кодом — уязвимости в библиотеках появляются постоянно.
