import re
import os
import pandas as pd
from openpyxl import load_workbook, Workbook
from fastapi import FastAPI, HTTPException, Response
import io
from urllib.parse import unquote

app = FastAPI()

# Базовые паттерны для поиска вхождения строки
patterns = [(r'(\d+)\s*шт', 'шт'),
            (r'(\d+)\s*гр', 'гр'),
            (r'(\d+)\s*г', 'г'),
            (r'(\d+)\s*таб', 'таб'),
            (r'(\d+)\s*табл', 'табл'),
            (r'(\d+(?:[,.]\d+)?)\s*мл', 'мл'),
            (r'(\d+(?:[,.]\d+)?)\s*л', 'л'),
            (r'(\d+(?:[,.]\d+)?)\s*кг', 'кг'),
            (r'(\d+)\s*gr', 'gr'),
            (r'(\d+)\s*g', 'g'),
            (r'(\d+)\s*ml', 'ml')]

# Паттерн Baby нужен для обработки памперсов
pattern_baby = r"(\d+)\s*шт"


def is_valid_value(value):
    """Проверяет, что значение соответствует критериям:
       - не пустое
       - числовое значение (после обработки)
       - длина не более 5 символов (для целых чисел)
       - значение больше 0"""
    if not value:
        return False

    try:
        # Преобразуем в строку и убираем лишние символы
        str_value = str(value).strip()
        if not str_value:
            return False

        # Проверяем длину строкового представления
        if len(str_value) > 5:
            return False

        # Пробуем преобразовать в число
        num_value = float(str_value.replace(',', '.'))

        # Проверяем, что число положительное
        if num_value <= 0:
            return False

        return True
    except (ValueError, TypeError):
        return False


def convert_units(value, unit):
    """Конвертирует единицы измерения:
       - литры в миллилитры (л → мл)
       - килограммы в граммы (кг → г)"""
    if not value or not unit:
        return None, None

    try:
        # Заменяем запятые на точки для корректного преобразования в float
        num_value = float(str(value).replace(',', '.'))

        if unit == 'л':
            converted_value = int(num_value * 1000)
            return (converted_value, 'мл') if is_valid_value(converted_value) else (None, None)
        elif unit == 'кг':
            converted_value = int(num_value * 1000)
            return (converted_value, 'г') if is_valid_value(converted_value) else (None, None)
        else:
            return (value, unit) if is_valid_value(value) else (None, None)
    except (ValueError, TypeError):
        return None, None


def extract_measurements(text):
    """Извлекает измерения из текста"""
    if not isinstance(text, str):
        return None, None

    text = text.lower()

    # Проверяем на подгузники
    if 'подгуз' in text or 'трус' in text:
        match = re.search(pattern_baby, text)
        if match:
            value = match.group(1)
            return (value, 'шт') if is_valid_value(value) else (None, None)

    # Проверяем остальные паттерны
    for pattern, unit in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            return (value, unit) if is_valid_value(value) else (None, None)

    return None, None


def main(new_file_path):
    # Читаем данные из SPR_DWH_SKU
    try:
        # Если файл Excel
        df = pd.read_excel(new_file_path, sheet_name='SPR_DWH_SKU')
        # Или если CSV:
        # df = pd.read_csv("SPR_DWH_SKU.csv", sep=';')
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    # Создаем новый DataFrame для результатов
    result_data = []

    for _, row in df.iterrows():
        # Используем .iloc для доступа по позиции
        unique_value = row.iloc[0] if len(row) > 0 else None
        text = str(row.iloc[1]) if len(row) > 1 else None
        group = str(row.iloc[2]).lower() if len(row) > 2 else None

        # Пропускаем пустые строки или строки с группой "прочее" или "наборы"
        if not text or (group and (group == "прочее" or group == "наборы")) or (unique_value == 'Общий итог'):
            continue

        value, unit = extract_measurements(text)

        # Конвертируем единицы измерения при необходимости
        if value and unit:
            value, unit = convert_units(value, unit)

        # Добавляем только если есть валидные значение и единица измерения
        if value and unit:
            result_data.append({
                'Артикул': unique_value,
                'Наименование': text,
                'Значение': value,
                'Единица_измерения': unit
            })

    return pd.DataFrame(result_data)


@app.get("/volumes")
def get_volumes(file_path: str):
    try:
        # Обрабатываем файл
        new_file_path = unquote(file_path)
        result_df = main(new_file_path)

        # Создаем файл в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=processed_result.xlsx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
