# check\_tt

## Назначение

Микросервис предназначен для асинхронной проверки Excel-файлов справочника торговых точек. Он ищет строки, в которых отсутствует значение в колонке `Нормализованный адрес`, и возвращает список таких файлов.

## Установка и запуск

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск сервиса

```bash
uvicorn check_tt:app --host 0.0.0.0 --port 8084
```

## API

### GET /tts

Проверяет список Excel-файлов на наличие пустых адресов в колонке `Нормализованный адрес`.

#### Параметры запроса

* `files_paths`: JSON-строка, содержащая список кортежей `[file_name, file_path]`.

#### Пример запроса

```http
GET /tts?files_paths=[["file1.xlsx", "/path/to/file1.xlsx"]]
```

#### Пример тела запроса (URI-encoded)

```
%5B%5B%22file1.xlsx%22%2C%22/path/to/file1.xlsx%22%5D%5D
```

#### Пример ответа

```json
{
  "result": ["file1.xlsx"]
}
```

## Примечания

* В каждом Excel-файле должен присутствовать лист с названием `DWH_dir_shop`.
* Колонка `Нормализованный адрес` обязательна.
* Пути к файлам должны быть URI-экодированы при передаче через URL.

## Зависимости

Основные используемые библиотеки:

* fastapi
* uvicorn
* pandas
* openpyxl

Полный список см. в `requirements.txt`.
