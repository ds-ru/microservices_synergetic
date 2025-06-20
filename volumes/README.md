# volumes

## Назначение

Микросервис предназначен для автоматического извлечения объема или количества (шт, мл, г, л, кг и т.д.) из текстовых наименований товаров. Работает с Excel-файлом справочника, в котором анализирует колонку с наименованием и определяет единицу измерения на основе регулярных выражений.

## Установка и запуск

```bash
pip install -r requirements.txt
uvicorn volumes:app --host 0.0.0.0 --port 8080
```

## API

### GET /volumes

Параметры запроса:

* `file_path` (str): путь к Excel-файлу в URL-кодировке

#### Пример запроса:

```http
GET /volumes?file_path=%5C%5Cserver%5Cpath%5Cfile.xlsx
```

#### Пример ответа:

Ответом является Excel-файл с колонками: `Артикул`, `Наименование`, `Значение`, `Единица_измерения`.

## Принцип работы

1. Открывается файл и загружается лист `SPR_DWH_SKU`.
2. Строки с группами "прочее" или "наборы", а также "Общий итог" исключаются.
3. Применяются регулярные выражения к наименованию товара:

   * Поиск количества в штуках: `шт`
   * Поиск массы: `г`, `гр`, `кг`, `g`, `gr`
   * Поиск объема: `мл`, `л`, `ml`
   * Обработка подгузников через `шт`
4. Значения `л` и `кг` конвертируются соответственно в `мл` и `г`
5. Возвращаются только валидные результаты (не пустые, числовые, не превышающие 5 символов длины)

## Примечания

* При обработке учитываются подгузники и другие специфические категории товаров.
* Для корректной работы файл должен содержать наименования товаров в первой колонке и группы в третьей.
* Обработка возможна как для `.xlsx`, так и с небольшими модификациями — для `.csv`.
* Пути передаются в URL-кодировке.

## Зависимости

Основные используемые библиотеки:

* fastapi
* uvicorn
* pandas
* openpyxl

Полный список см. в `requirements.txt`.
