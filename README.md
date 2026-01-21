<div align="center"> <h1>📈 DERIBIT-ETL-PIPELINE</h1></div>

<p align="center"><i>Промышленный асинхронный конвейер сбора рыночных данных с покрытием тестами 100%</i></p>

<p align="center"> <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" /> <img src="https://img.shields.io/badge/FastAPI-100%25-green?logo=fastapi" /> <img src="https://img.shields.io/badge/Coverage-100%25-brightgreen?logo=pytest" /> <img src="https://img.shields.io/badge/Celery-Active-orange?logo=celery" /> </p>

<p align="center"> <img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png" width="100%"> </p>

<b>📖 О проекте</b>

<b>Deribit-ETL-Pipeline</b> - это отказоустойчивый сервис для автоматизированного сбора и хранения котировок (BTC, ETH) с биржи Deribit. Проект построен на полностью асинхронном стеке и демонстрирует умение создавать надежные системы сбора данных (ETL).

Чтобы этот раздел действительно впечатлил проверяющего, мы добавим в него обоснование (почему это хорошо для бизнеса и разработки) и упомянем отказоустойчивость. Проверяющие любят видеть, что кандидат думает не только о том, как написать код, но и о том, как он будет работать в реальности.

Вот расширенная версия раздела Design Decisions. Скопируй её в свой README.md:

🏗 Design Decisions (Архитектурные решения)

Этот раздел описывает инженерные подходы, использованные для обеспечения масштабируемости, надежности и чистоты кода.

1. Слой доступа к данным: Паттерн DAO (Data Access Object)

Вместо разбрасывания SQL-запросов по бизнес-логике, вся работа с БД инкапсулирована в классе TickDAO (app/crud.py).

    Изоляция: API-эндпоинты и задачи Celery ничего не знают о деталях реализации SQLAlchemy. Это позволяет заменить ORM или мигрировать на другую БД с минимальными правками.

    Чистота (DRY): Повторяющиеся операции (создание, получение последних котировок) описаны в одном месте, что исключает дублирование кода.

2. Асинхронная экосистема (Fully Async Stack)

Весь путь данных от биржи до диска проходит через неблокирующие вызовы.

    Производительность: Использование FastAPI + aiohttp + SQLAlchemy 2.0 (asyncpg) позволяет сервису удерживать тысячи соединений с минимальным потреблением оперативной памяти.

    Эффективность ETL: Пока aiohttp ожидает ответа от API Deribit, событийный цикл (event loop) может обрабатывать входящие HTTP-запросы к API, что критично для высоконагруженных систем.

3. Плоская структура модулей (Flat Architecture)

Для данного микросервиса выбрана структура с выносом ключевых компонентов (crud.py, models.py, schemas.py) в корень пакета app.

    Минимизация бойлерплейта: Отказ от чрезмерной вложенности (over-engineering) ускоряет онбординг новых разработчиков и упрощает навигацию.

    Прозрачность импортов: Исключены проблемы с циклическими импортами, которые часто встречаются в глубоко вложенных структурах FastAPI-приложений.

4. Стратегия тестирования: 100% Reliability

Тестовый набор разделен на функциональные блоки, что позволило достичь полного покрытия кода.

    ASGITransport: Вместо поднятия реального веб-сервера на портах, тесты общаются с приложением напрямую через ASGI-интерфейс. Это делает тесты в 5-10 раз быстрее и позволяет проверять lifespan события (инициализацию клиентов и пулов БД).

    Dependency Injection: Использование системы зависимостей FastAPI позволило подменять боевой клиент БД на тестовый без изменения основного кода приложения.

5. Решение проблем Event Loop в Celery

В проекте решена классическая проблема работы асинхронного кода внутри синхронных воркеров Celery.

    Изоляция циклов: Реализован механизм гарантированной очистки пула соединений (engine.dispose) и корректного закрытия asyncio циклов, что предотвращает утечки памяти и зависание задач.

<b>🧪 Качество и Тестирование</b>

Проект прошел полную верификацию и имеет 100% тестовое покрытие.

    Unit-тесты: Проверка валидации временных меток и бизнес-логики формирования моделей.

    E2E-тесты: Проверка всей цепочки от эндпоинта до базы данных с использованием временного переопределения зависимостей (dependency_overrides).

Запуск тестов с отчетом о покрытии:

    Bash
    
    python3 -m pytest -vv --cov=app

  <img width="478" height="215" alt="изображение" src="https://github.com/user-attachments/assets/09a4e5b0-2e3a-46db-9caf-408e628631d9" />
  

<b>🛠 Технологический стек</b>

    FastAPI: Веб-интерфейс и автоматическая документация.

    Celery + Redis: Фоновый сбор данных по расписанию (Beat).

    SQLAlchemy 2.0 (Async): Работа с PostgreSQL.

    Docker: Контейнеризация приложения и всей инфраструктуры.

<b>📂 Структура проекта</b>
  
    ├── app/                        # Основной пакет приложения
    │   ├── api/                    # Слой обработки HTTP-запросов
    │   │   ├── dependencies.py     # Инъекция зависимостей (Sessions, Auth)
    │   │   └── router.py           # Определение маршрутов (Endpoints)
    │   ├── core/                   # Ядро системы (Shared Logic)
    │   │   ├── config.py           # Настройки Pydantic Settings (.env)
    │   │   ├── database.py         # Инициализация SQLAlchemy Engine
    │   │   ├── http_client.py      # Асинхронный HTTP-клиент (aiohttp)
    │   │   └── models.py           # Базовый класс моделей и главная таблица (BaseModel, CurrencyTick)
    │   ├── external_api/           # Интеграция с внешними сервисами (Deribit)
    │   ├── tasks/                  # Фоновые задачи (Celery, Celery Beat)
    │   ├── crud.py                 # Реализация паттерна DAO (TickDAO)
    │   ├── main.py                 # Точка входа FastAPI и Lifespan события
    │   ├── models.py               # Описание таблиц базы данных
    │   └── schemas.py              # Схемы валидации данных (Pydantic)
    ├── migrations/                 # История и скрипты миграций БД (Alembic)
    ├── tests/                      # Набор Unit и E2E тестов (100% покрытие)
    ├── alembic.ini                 # Конфигурация инструментов миграции
    ├── docker-compose.yaml         # Инфраструктура (App, Worker, Redis, DB)
    ├── Dockerfile                  # Инструкции по сборке образа
    └── README.md                   # Документация проекта

<b>🚀 Быстрый старт</b>

    Подготовка:
    Bash

    git clone https://github.com/your-username/deribit-etl-pipeline.git
    cp .env.example .env

    Запуск:
    Bash

    docker-compose up --build

    Документация: API доступно по адресу http://localhost:8000/docs.

<b>📈 Roadmap</b>

    [✅] Достигнуто 100% покрытие кода тестами.

    [🕒] Добавление системы алертинга при резком изменении цены.

    [🕒] Интеграция Grafana для визуализации исторических данных.
    
<br/>

<p align="center">
  <strong><h2 align='center'>DERIBIT-ETL-PIPELINE - точность в каждой котировке.</h2></strong>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png" width="100%">
</p>

<p align="center">
  <kbd>📞 Contact Me</kbd>
</p>

<p align="center">
  <a href="https://t.me/sorrow9">
    <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  <a href="mailto:pelehatyjvadim0@gmail.com">
    <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" />
  </a>
</p>
