# Multi-Service Dashboard

## Описание

**Multi-Service Dashboard** — это веб-приложение, созданное с использованием Streamlit (фронтенд) и FastAPI (бэкенд), предназначенное для централизации и автоматизации различных задач по обработке и анализу данных, связанных с продажами в торговых сетях (онлайн и офлайн).

Приложение предоставляет единый интерфейс для запуска нескольких микросервисов, каждый из которых отвечает за свою специфическую функцию, упрощая рутинные операции аналитиков и менеджеров.

## Основные Возможности (Сервисы)

* **Обработка объемов (Порт 8080):** Извлечение информации об объеме/весе/количестве из наименований товаров.
* **Обработка линеек (Порт 8081):** Определение принадлежности товаров к специфическим линейкам ('Baby', 'Pump').
* **Парсер наименований ДМ (Порт 8082):** Получение актуальных наименований товаров с сайта detmir.ru по SKU.
* **Парсер Globus (Порт 8083):** Сбор информации о товарах (бренд, наименование, объем) с сайта online.globus.ru по SKU (асинхронный).
* **Проверка пустых ТТ (Порт 8084):** Проверка наличия пустых адресов в справочниках торговых точек офлайн-сетей.

## Технологический стек

* **Фронтенд:** Python, Streamlit
* **Бэкенд:** Python, FastAPI, Uvicorn
* **Обработка данных:** Pandas, Openpyxl
* **Веб-скрапинг/Запросы:** Requests, Aiohttp, BeautifulSoup4
* **Прочее:** JSON, re (Регулярные выражения)

## Структура Репозитория (Предполагаемая)

Репозиторий содержит отдельные директории для фронтенда и каждого бэкенд-микросервиса:

* `maulti_web_service/`: Фронтенд-приложение Streamlit (`main.py`, `file_paths.json`, `requirements.txt`).
* `Volumes/`: Бэкенд-сервис "Обработка объемов" (`main_v2_volume.py`, `requirements.txt`).
* `Prod_lines/`: Бэкенд-сервис "Обработка линеек" (`main.py`, `requirements.txt`).
* `Detskiy_Mir_Parser/`: Бэкенд-сервис "Парсер ДМ" (`main_v2_fastapi.py`, `requirements.txt`).
* `Globus_Parser/`: Бэкенд-сервис "Парсер Globus" (`main.py`, `requirements.txt`).
* `outlet_control/`: Бэкенд-сервис "Проверка пустых ТТ" (`main.py`, `requirements.txt`).
* `micro_start.bat`: Скрипт для запуска всех сервисов на Windows.
* `README.md`: Этот файл.

## Предварительные требования

* Python 3.x
* Менеджер пакетов `pip`
* Доступ к сетевым ресурсам (файлам Excel), указанным в `file_paths.json`, с машины, где будут запущены бэкенд-сервисы.

## Конфигурация

Основная конфигурация путей к файлам данных сетей находится в файле `file_paths.json` в директории фронтенда (`multi_web_service/`).

```json
{
  "files": [
    {
      "name": "Имя сети (отображается в UI)",
      "path": "\\сервер\\путь\\к\\файлу.xlsx",
      "segment": "online" // или "offline"
    }
  ]
}
```

## Запуск всех сервисов (Windows)

В проект включён вспомогательный `.bat`-файл для автоматического запуска всех микросервисов и Streamlit-интерфейса в отдельных окнах командной строки:

```bat
@echo off
title Запуск микросервисов

:: Запуск первого сервиса (Streamlit)
start "Multi Web Service" cmd /k "cd C:\Users\speransky_d\PycharmProjects\maulti_web_service && streamlit run main.py"

:: Запуск остальных сервисов (FastAPI/обычные Python скрипты)
start "Detskiy Mir Parser" cmd /k "cd C:\Users\speransky_d\PycharmProjects\Detskiy_Mir_Parser && python main_v2_fastapi.py"
start "Globus Parser" cmd /k "cd C:\Users\speransky_d\PycharmProjects\Globus_Parser && python main.py"
start "Outlet Control" cmd /k "cd C:\Users\speransky_d\PycharmProjects\outlet_control && python main.py"
start "Prod Lines" cmd /k "cd C:\Users\speransky_d\PycharmProjects\Prod_lines && python main.py"
start "Volumes" cmd /k "cd C:\Users\speransky_d\PycharmProjects\Volumes && python main_v2_volume.py"

echo Все микросервисы запущены!
pause
```

Сценарий открывает отдельное окно для каждого сервиса, обеспечивая независимую и параллельную работу всех компонентов.
