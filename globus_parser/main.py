from asyncio import gather, Semaphore
import json
from bs4 import BeautifulSoup
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
import io
import aiohttp


app = FastAPI()


# Рекурсивная функция для поиска ключа "brand"
def find_brand(data):
    # Если data является словарем
    if isinstance(data, dict):
        # Проверяем, есть ли ключ "brand"
        if "brand" in data:
            return data["brand"]
        # Рекурсивно проверяем все значения в словаре
        for key, value in data.items():
            result = find_brand(value)
            if result:
                return result
    # Если data является списком
    elif isinstance(data, list):
        # Рекурсивно проверяем все элементы списка
        for item in data:
            result = find_brand(item)
            if result:
                return result
    # Если ключ "brand" не найден
    return None


def find_volume_ml(data):
    """Рекурсивная функция для поиска объема в миллилитрах"""
    if isinstance(data, dict):
        # Проверяем атрибут объема в мл
        if data.get("id") == "atr_calc_if_volume_range_in_ml":
            value = data.get("value", [None])[0]
            return (value, "мл") if value else None

        # Рекурсивный поиск в значениях словаря
        for value in data.values():
            result = find_volume_ml(value)
            if result:
                return result

    elif isinstance(data, list):
        # Рекурсивный поиск в элементах списка
        for item in data:
            result = find_volume_ml(item)
            if result:
                return result

    return None


def find_volume_gram(data):
    """Рекурсивная функция для поиска веса в граммах (с конвертацией из кг)"""
    if isinstance(data, dict):
        # Проверяем выбранный вес
        if data.get("is_selected", False) and "вес" in str(data.get("name", "")).lower():
            value = data.get("value")
            try:
                return (float(value) * 1000, "г") if value else None
            except (ValueError, TypeError):
                return None

        # Рекурсивный поиск в значениях словаря
        for value in data.values():
            result = find_volume_gram(value)
            if result:
                return result

    elif isinstance(data, list):
        # Рекурсивный поиск в элементах списка
        for item in data:
            result = find_volume_gram(item)
            if result:
                return result

    return None


def find_volume_piece(data):
    """Рекурсивная функция для поиска количества в штуках"""
    if isinstance(data, dict):
        # Проверяем атрибут количества в упаковке
        if data.get("id") == "atr_quantity_in_package":
            value = data.get("value", [None])[0]
            return (value, "шт") if value else None

        # Рекурсивный поиск в значениях словаря
        for value in data.values():
            result = find_volume_piece(value)
            if result:
                return result

    elif isinstance(data, list):
        # Рекурсивный поиск в элементах списка
        for item in data:
            result = find_volume_piece(item)
            if result:
                return result

    return None


def find_name(data):
    if isinstance(data, dict):
        if "product" in data:
            return data["product"]["name"]
        for key, value in data.items():
            result = find_name(value)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_name(item)
            if result is not None:
                return result
    return None


async def fetch(session: aiohttp.ClientSession, url: str, sku_id: str, semaphore: Semaphore):
    async with semaphore:
        try:
            async with session.get(url) as response:
                text = await response.text()
                return text, sku_id
        except Exception as e:
            print(f"Ошибка при запросе {sku_id}: {str(e)}")
            return None, sku_id


async def process_page(text: str, sku_id: str):
    try:
        if not text:
            return None

        soup = BeautifulSoup(text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')

        if not script_tag:
            return None

        data = json.loads(script_tag.string)

        brand_data = find_brand(data)
        name_data = find_name(data)
        volume_data = find_volume_ml(data) or find_volume_gram(data) or find_volume_piece(data)

        return {
            'Код SKU': sku_id,
            'Наименование': name_data,
            'Бренд': brand_data['name'] if brand_data else None,
            'Объем': volume_data[0] if volume_data else None,
            'Ед. изм': volume_data[1] if volume_data else None
        }
    except Exception as e:
        print(f"Ошибка обработки {sku_id}: {str(e)}")
        return None


async def main_async(min_row: int, batch_size: int = 10):
    file_path = r"\\10.5.0.20\аналитики\PBI\ПРОДАЖИ\GLOBUS\СправочникиПОЛН.xlsx"
    df = pd.read_excel(file_path, sheet_name="SPR_DWH_SKU")

    df = df.iloc[int(min_row) - 1:].copy()
    df = df[(df['Уник. названия групп'] != 'Прочее') & (df['Код SKU'] != 'Общий итог')]

    result = []
    semaphore = Semaphore(10)  # Ограничиваем количество одновременных запросов

    async with aiohttp.ClientSession(headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }) as session:
        tasks = []
        for sku_id in df['Код SKU']:
            url = f"https://online.globus.ru/products/{sku_id}_ST/"
            tasks.append(fetch(session, url, sku_id, semaphore))

        # Обрабатываем результаты батчами
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            responses = await gather(*batch)

            for text, sku_id in responses:
                if text:
                    processed = await process_page(text, sku_id)
                    if processed:
                        result.append(processed)
                        print(f"Обработано: {sku_id} | Бренд: {processed['Бренд']} | "
                              f"Объем: {processed['Объем'] or '-'} "
                              f"{processed['Ед. изм'] or ''}")

    return pd.DataFrame(result)


@app.get("/globus")
async def get_volumes(min_row: str):
    try:
        result_df = await main_async(min_row)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=globus_products.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
