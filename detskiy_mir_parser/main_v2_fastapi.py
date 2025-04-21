import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import os
from openpyxl import load_workbook, Workbook
from fastapi import FastAPI, HTTPException, Response
import io
from urllib.parse import unquote

app = FastAPI()

def main(min_row):
    df = pd.read_excel(r"\\10.5.0.20\аналитики\PBI\ПРОДАЖИ\ДМ\СправочникиПОЛН.xlsx", sheet_name="SPR_DWH_SKU")
    df = df.iloc[int(min_row) - 1:].copy()
    df = df[(df['Уник. названия групп'] != 'Прочее') & (df['Код SKU'] != 'Общий итог')]

    result_df = []

    for _, row in df.iterrows():
        # URL и заголовки запроса
        url = f"https://www.detmir.ru/search/results/?qt={row['Код SKU']}&searchType=auto&searchMode=common"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36",
        }

        try:
            # Отправка GET-запроса к странице
            response = requests.get(url, headers=headers)

            # Проверка успешного ответа
            if response.status_code == 200:
                # Используем BeautifulSoup для обработки HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                # Поиск всех <script> тегов
                script_datas = soup.find_all("script")
                for script_data in script_datas:
                    if script_data.string and 'appData' in script_data.string:
                        try:
                            json_text = script_data.string
                            # Извлечение данных, используя простое регулярное выражение
                            json_text = json_text.split('window.appData = JSON.parse(')[-1][
                                        :-2]  # Получаем часть после JSON.parse
                            json_text = json_text.replace(r'\\\"', '')
                            json_text = json_text.replace(r'\\"', '')
                            json_text = json_text.replace(r'\"', '"')  # Убираем экранирование
                            json_text = json_text[1:]
                            app_data = json.loads(json_text)  # Преобразуем в словарь Python
                            # print(json.dumps(app_data, indent=4), "\n\n\n\n")
                            break  # Завершаем после первого совпадения
                        except Exception as e:
                            print("Ошибка при обработке JSON:", e)

                # Поиск нужного товара по SKU и добавление данных в результаты
                for suggestion in app_data['search']['data']['suggestions']:
                    if suggestion['type'] == 'product':
                        product = suggestion['filter'].get('product')
                        # if product and product.get('code') == row:
                        title_found = product['title']
                        result_df.append({'Артикул': row['Код SKU'],
                                          'Наименование': row['Название SKU в сети'],
                                          'Наименование новое': title_found})
                        break
            else:
                print(f"Ошибка при загрузке страницы: {response.status_code}")

        except Exception as e:
            print(f"Ошибка при обработке SKU {row}: {e}")

    return pd.DataFrame(result_df)


@app.get("/detskiy_mir")
def get_lines(min_row: str):
    try:
        # Обрабатываем файл
        result_df = main(min_row)

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
    uvicorn.run(app, host="0.0.0.0", port=8082)
