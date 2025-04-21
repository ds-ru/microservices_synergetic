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