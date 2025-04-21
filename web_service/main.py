import json
import os
from http.client import responses
from urllib.parse import quote
import streamlit as st
import requests

# Конфигурация страницы
st.set_page_config(
    page_title="Multi-Service Dashboard",
    page_icon=":wrench:",
    layout="wide"
)

# Стили CSS для красивого оформления
st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border-radius: 8px;
    }
    .stTextInput>div>div>input {
        padding: 10px;
    }
    .css-1v0mbdj {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Заголовок с иконкой
st.title(":wrench: Multi-Service Dashboard")
st.markdown("---")

# Боковое меню для выбора сервиса
service = st.sidebar.selectbox(
    "Выберите сервис",
    ["Обработка объемов", "Обработка линеек", "Парсер наименований ДМ", "Парсер Globus", "Проверка пустых ТТ","Общая проверка"],
    index=0
)

# Сервис анализа объемов
if service == "Обработка объемов":
    st.markdown("""
    <h2>📊 Обработка объемов товаров <span style='color: white;'>(8080)</span></h2>
    """, unsafe_allow_html=True)

    # Загрузка конфигурации
    try:
        with open('file_paths.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            networks = config["files"]
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации: {str(e)}")
        st.stop()

    # Выбор сети
    option = st.selectbox(
        "Выберите сеть для анализа",
        [net["name"] for net in networks],
        index=0
    )

    if st.button("Анализировать"):
        selected = next((net for net in networks if net["name"] == option), None)

        if not selected:
            st.error("Выбранная сеть не найдена в конфигурации")
        file_path = selected["path"]
        response = requests.get('http://localhost:8080/volumes', params={'file_path': file_path})
        if response.status_code == 200:
            st.success("Файл успешно обработан!")

            # Скачивание результата
            output_path = f"processed_result.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Скачать результат",
                    data=f,
                    file_name=output_path,
                    mime="application/vnd.ms-excel"
                )

            os.remove(output_path)
        else:
            st.error(f"Ошибка: {response.text}")
    else:
        st.error("Выберите сеть!")

# Сервис парсера 1
elif service == "Обработка линеек":
    st.markdown("""
        <h2>🔍 Обработка линеек товаров <span style='color: white;'>(8081)</span></h2>
        """, unsafe_allow_html=True)

    # Загрузка конфигурации
    try:
        with open('file_paths.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            networks = config["files"]
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации: {str(e)}")
        st.stop()

    # Выбор сети
    option = st.selectbox(
        "Выберите сеть для анализа",
        [net["name"] for net in networks],
        index=0
    )

    if st.button("Анализировать"):
        selected = next((net for net in networks if net["name"] == option), None)

        if not selected:
            st.error("Выбранная сеть не найдена в конфигурации")
        file_path = selected["path"]
        response = requests.get('http://localhost:8081/lines', params={'file_path': file_path})
        if response.status_code == 200:
            st.success("Файл успешно обработан!")

            # Скачивание результата
            output_path = f"processed_result.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Скачать результат",
                    data=f,
                    file_name=output_path,
                    mime="application/vnd.ms-excel"
                )

            os.remove(output_path)
        else:
            st.error(f"Ошибка: {response.text}")
    else:
        st.error("Выберите сеть!")


# Сервис обработки Excel 1
elif service == "Парсер наименований ДМ":
    st.markdown("""
            <h2>🧸 Парсер наименований ДМ <span style='color: white;'>(8082)</span></h2>
            """, unsafe_allow_html=True)

    min_row = st.number_input(
        "Введите номер строки с которой нужно начать",
        min_value=0,
        value=0,
        step=1
    )

    if st.button("Запустить парсинг"):
        response = requests.get('http://localhost:8082/detskiy_mir', params={'min_row': min_row})
        if response.status_code == 200:
            st.success("Файл успешно обработан!")

            # Скачивание результата
            output_path = f"processed_result.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Скачать результат",
                    data=f,
                    file_name=output_path,
                    mime="application/vnd.ms-excel"
                )

            os.remove(output_path)
        else:
            st.error(f"Ошибка: {response.text}")

elif service == "Парсер Globus":
    st.markdown("""
            <h2>🌎 Парсер Globus (Бренды, наименования, объемы, единицы измерения) <span style='color: white;'>(8083)</span></h2>
            """, unsafe_allow_html=True)

    min_row = st.number_input(
        "Введите номер строки с которой нужно начать",
        min_value=0,
        value=0,
        step=1
    )

    if st.button("Запустить парсинг"):
        response = requests.get('http://localhost:8083/globus', params={'min_row': min_row})
        if response.status_code == 200:
            st.success("Файл успешно обработан!")

            # Скачивание результата
            output_path = f"processed_result.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Скачать результат",
                    data=f,
                    file_name=output_path,
                    mime="application/vnd.ms-excel"
                )

            os.remove(output_path)
        else:
            st.error(f"Ошибка: {response.text}")

elif service == "Проверка пустых ТТ":
    st.markdown("""
                <h2>Проверка сетей на пустые ТТ <span style='color: white;'>(8084)</span></h2>
                """, unsafe_allow_html=True)

    # Инициализация состояния сессии
    if 'selected_networks' not in st.session_state:
        st.session_state.selected_networks = []

    # Загрузка конфигурации
    try:
        with open('file_paths.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            networks = config["files"]
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации: {str(e)}")
        st.stop()

    # Выбор сетей (исправлен фильтр на "online")
    available_nets = [net["name"] for net in networks if net["segment"] == "offline"]

    # Поле выбора сетей
    set_stores_net = st.multiselect(
        "Выберите сети для анализа",
        available_nets,
        default=st.session_state.selected_networks,
        placeholder="Выберите одну или несколько сетей"
    )
    st.session_state.selected_networks = set_stores_net

    # Кнопки в одной строке с одинаковым размером
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Выбрать все",
                     help="Выбрать все доступные сети",
                     use_container_width=True,
                     key="select_all_btn"):
            st.session_state.selected_networks = available_nets.copy()
            st.rerun()
    with col2:
        analyze_clicked = st.button("Анализировать",
                                    type="primary",
                                    use_container_width=True,
                                    key="analyze_btn")

    # Обработка анализа
    if analyze_clicked:
        if not st.session_state.selected_networks:
            st.warning("Пожалуйста, выберите хотя бы одну сеть для анализа")
            st.stop()

        # Подготовка параметров для запроса
        selected_files = [(net['name'], quote(net['path']))
                          for net in networks if net['name'] in st.session_state.selected_networks]

        # Преобразуем в формат, который понимает FastAPI
        params = {"files_paths": json.dumps(selected_files)}

        try:
            with st.spinner("Идет анализ данных..."):
                response = requests.get('http://localhost:8084/tts', params=params)
                response.raise_for_status()
                result = response.json()

            st.success("Анализ завершён!")

            # Проверка результата
            if isinstance(result, dict) and 'result' in result:
                if isinstance(result['result'], list) and len(result['result']) > 0:
                    st.markdown("**По данным сетям есть ненормализованные адреса**")
                    st.json(result)
                else:
                    st.markdown("**По всем сетям адреса нормализованы**")
            else:
                st.markdown("**Не удалось обработать результат анализа**")
                st.json(result)  # Показываем сырой результат для диагностики

        except requests.exceptions.RequestException as e:
            st.error(f"Ошибка при запросе к API: {str(e)}")

# Общий статус сервисов
st.sidebar.markdown("---")
st.sidebar.subheader("Статус сервисов")
service_status = {
    "Обработка объемов": "🟢 Работает",
    "Обработка линеек": "🟢 Работает",
    "Парсер наименований ДМ": "🟢 Работает",
    "Парсер Globus": "🟢 Работает",
    "Проверка пустых ТТ": "🟢 Работает",
    "Общая проверка": "🔴 Недоступен"
}

for service_name, status in service_status.items():
    st.sidebar.markdown(f"{service_name}: {status}")

# Футер
st.markdown("---")
st.markdown("© 2025 Multi-Service Dashboard | [Техподдержка](mailto:speranskiy_d@synergetic.ru)")