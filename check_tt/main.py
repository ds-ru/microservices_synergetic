import json
from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from urllib.parse import unquote
from typing import List, Tuple

app = FastAPI()


async def process_files(files_paths: List[Tuple[str, str]]) -> List[str]:
    result = []
    for file_name, file_path in files_paths:
        try:
            print(f"Processing {file_name} from {file_path}")
            df = pd.read_excel(unquote(file_path), sheet_name='DWH_dir_shop')

            # Правильная проверка на NaN значений
            if df['Нормализованный адрес'].isna().any():
                result.append(file_name)
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
            return None

    return result


@app.get("/tts")
async def check_tts(files_paths: str = Query(...)):
    try:
        files = json.loads(files_paths)  # Десериализуем JSON
        result = await process_files(files)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8084)