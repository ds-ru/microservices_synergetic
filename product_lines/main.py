import re
import os
import pandas as pd
from openpyxl import load_workbook, Workbook
from fastapi import FastAPI, HTTPException, Response
import io
from urllib.parse import unquote

app = FastAPI()


# Массив с ключевыми словами детских товаров
baby_str = [
    "baby", "kids", "детский", "детей", "девочек", "мальчиков", "младенцев", "новорожд", "малышей",
    "ребенок", "ребенка", "ребенку", "ребенком", "ребенке", "малыш", "малыша", "малышу", "малышом", "малыше",
    "младенец", "младенца", "младенцу", "младенцем", "младенце", "новорожденный", "новорожденного",
    "новорожденному", "новорожденным", "новорожденном", "детское", "детские", "дошкольник", "дошкольника",
    "дошкольнику", "дошкольником", "дошкольнике", "школьник", "школьника", "школьнику", "школьником",
    "школьнике", "подросток", "подростка", "подростку", "подростком", "подростке"
]

# Массив с уникальными названиями групп детских товаров
baby_group = [
    "влажн. салфетки baby", "влажн. туал. бумага", "средства для купания baby", "жидкое мыло baby",
    "кремы для детей", "твердое мыло baby", "наборы уход baby", "пены для ванны baby",
    "подгузники", "шампуни baby", "доп. уход за волосами baby"
]

# Массив с ключевыми словами для Pump зубных паст
pump_line = ["дозатор", "помпа", "помпой", "pump", "памп"]


def main(new_file_path):
    try:
        df = pd.read_excel(new_file_path, sheet_name="SPR_DWH_SKU")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    df = df[(df['Уник. названия групп'] != 'Прочее') & (df['Линейка уровень 2'].notna()) & (df['Код SKU'] != 'Общий итог')]

    result_df = []

    for _, row in df.iterrows():
        unique_value = row.iloc[0] if len(row) > 0 else None
        text = str(row.iloc[1]) if len(row) > 1 else None

        flag = False

        for baby_word in baby_str:
            if baby_word in text:
                result_df.append({'Артикул': unique_value, 'Наименование': text,'Линейка': 'Baby'})
                flag = True

        if not flag:
            for pump_word in pump_line:
                if pump_word in text:
                    result_df.append({'Артикул': unique_value, 'Наименование': text,'Линейка': 'Pump'})

    return pd.DataFrame(result_df)



@app.get("/lines")
def get_lines(file_path: str):
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
    uvicorn.run(app, host="0.0.0.0", port=8081)
