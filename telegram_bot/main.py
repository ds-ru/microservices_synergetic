import logging
import telebot
from telebot import types
import pandas as pd
import json
import os
import time
from collections import defaultdict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат сообщений
    handlers=[
        logging.FileHandler("bot.log", "a", "utf-8"),  # Запись в файл
        logging.StreamHandler()  # Вывод в консоль
    ]
)

API_TOKEN = ""
ADMIN_ID =  # Замените на ID администратора

bot = telebot.TeleBot(API_TOKEN)

# Пути к данным
REGISTRATION_FILE = 'registrations.json'
FILE_PATHS_FILE = 'file_paths.json'

# Базовые данные для регистрации
DEFAULT_REGISTRATION_DATA = {
    "pending": {},
    "registered": {}
}

# Лимиты для защиты от спама и DDoS
USER_REQUEST_LIMITS = defaultdict(int)  # Счетчик запросов пользователя
MAX_REQUESTS_PER_MINUTE = 10  # Максимальное количество запросов в минуту

# Функция для загрузки или создания файла с данными
def load_or_create_file(file_path, default_data):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(default_data, file, indent=4, ensure_ascii=False)
        return default_data
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                logging.info(f"Файл {file_path} успешно загружен.")
                return json.load(file)
        except json.JSONDecodeError:
            with open(file_path, 'w', encoding='utf-8') as file:
                logging.warning(f"Файл {file_path} поврежден. Создан новый файл с данными по умолчанию.")
                json.dump(default_data, file, indent=4, ensure_ascii=False)
            return default_data

# Загрузка данных о регистрации
registration_data = load_or_create_file(REGISTRATION_FILE, DEFAULT_REGISTRATION_DATA)

# Сохранение данных о регистрации
def save_registration_data():
    with open(REGISTRATION_FILE, 'w', encoding='utf-8') as file:
        json.dump(registration_data, file, indent=4, ensure_ascii=False)

# Проверка лимита запросов
def check_request_limit(user_id):
    current_time = time.time()
    if USER_REQUEST_LIMITS[user_id] >= MAX_REQUESTS_PER_MINUTE:
        return False
    USER_REQUEST_LIMITS[user_id] += 1
    return True

# Сброс счетчика запросов каждую минуту
def reset_request_limits():
    while True:
        time.sleep(60)
        USER_REQUEST_LIMITS.clear()

# Запуск сброса счетчика в отдельном потоке
import threading
threading.Thread(target=reset_request_limits, daemon=True).start()

def update_keyboard(user_id, message_text=None):
    """
    Обновляет клавиатуру для пользователя.
    :param user_id: ID пользователя
    :param message_text: Текст сообщения (опционально)
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Получить отчет"))

    if message_text:
        bot.send_message(user_id, message_text, reply_markup=keyboard)
    else:
        bot.send_message(user_id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def cmd_start(message):
    if not check_request_limit(message.chat.id):
        bot.send_message(message.chat.id, "Слишком много запросов. Пожалуйста, подождите.")
        return
    if str(message.chat.id) not in registration_data["registered"]:
        bot.send_message(
            message.chat.id,
            "Привет! Я бот для обработки данных о товарах.\n"
            "Для регистрации напишите /register.\n"
            "В случае ошибки попробуйте /reset."
        )
    else:
        update_keyboard(message.chat.id, "Вы можете воспользоваться кнопкой ниже для получения отчета:")

# Команда /reset
@bot.message_handler(commands=['reset'])
def cmd_reset(message):
    if not check_request_limit(message.chat.id):
        logging.warning(f"Пользователь {message.chat.id} превысил лимит запросов.")
        bot.send_message(message.chat.id, "Слишком много запросов. Пожалуйста, подождите.")
        return
    user_id = str(message.chat.id)
    if user_id in registration_data["registered"]:
        logging.info(f"Чат пользователя {message.chat.id} перезапущен.")
        bot.send_message(user_id, "Попытка перезапуска! Если появилась кнопка 'Получить отчет', то всё прошло успешно! :)")
        update_keyboard(message.chat.id, "Бот перезапущен! Используйте кнопку для отчета:")

# Команда /register
@bot.message_handler(commands=['register'])
def cmd_register(message):
    if not check_request_limit(message.chat.id):
        logging.warning(f"Пользователь {message.chat.id} превысил лимит запросов.")
        bot.send_message(message.chat.id, "Слишком много запросов. Пожалуйста, подождите.")
        return
    user_id = str(message.chat.id)
    if user_id in registration_data["registered"]:
        update_keyboard(message.chat.id, "Вы уже зарегистрированы!")
    elif user_id in registration_data["pending"]:
        logging.info(f"Пользователь @{message.from_user.username} отправил запрос на регистрацию.")
        bot.send_message(user_id, "Ваш запрос на регистрацию уже отправлен. Ожидайте подтверждения.")
    else:
        msg = bot.send_message(user_id, "Введите ваше ФИО для регистрации:")
        bot.register_next_step_handler(msg, process_fio)

# Обработка ввода ФИО
def process_fio(message):
    fio = message.text.strip()
    user_id = str(message.chat.id)
    registration_data["pending"][user_id] = {"fio": fio}
    save_registration_data()
    bot.send_message(
        ADMIN_ID,
        f"Новый запрос на регистрацию:\n\n"
        f"ФИО: {fio}\n"
        f"Имя пользователя: @{message.from_user.username}\n"
        f"ID пользователя: {user_id}\n\n"
        f"Подтвердить регистрацию?\n"
        f"/confirm_{user_id} для подтверждения\n"
        f"/reject_{user_id} для отклонения"
    )
    bot.send_message(user_id, "Ваш запрос на регистрацию отправлен администратору. Ожидайте подтверждения.")

# Подтверждение регистрации администратором
@bot.message_handler(func=lambda message: message.text.startswith('/confirm_'))
def cmd_confirm(message):
    try:
        user_id = message.text.split('_')[1]
        if user_id in registration_data["pending"]:
            fio = registration_data["pending"][user_id]["fio"]
            registration_data["registered"][user_id] = fio
            del registration_data["pending"][user_id]
            save_registration_data()
            bot.send_message(user_id, f"Регистрация подтверждена! Добро пожаловать, {fio}.")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(types.KeyboardButton("Получить отчет"))
            bot.send_message(user_id, "Вы можете воспользоваться кнопкой ниже для получения отчета:",
                             reply_markup=keyboard)
            bot.send_message(ADMIN_ID, f"Пользователь {fio} (ID: {user_id}) успешно зарегистрирован.")
            logging.info(f"Регистрация пользователя {fio} (ID: {user_id}) подтверждена.")
        else:
            bot.send_message(ADMIN_ID, "Запрос на регистрацию с указанным ID не найден.")
            logging.warning(f"Запрос на регистрацию с ID {user_id} не найден.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Произошла ошибка: {str(e)}")
        logging.error(f"Ошибка при подтверждении регистрации: {str(e)}")

# Отклонение регистрации администратором
@bot.message_handler(func=lambda message: message.text.startswith('/reject_'))
def cmd_reject(message):
    try:
        user_id = message.text.split('_')[1]
        if user_id in registration_data["pending"]:
            fio = registration_data["pending"][user_id]["fio"]
            del registration_data["pending"][user_id]
            save_registration_data()
            bot.send_message(user_id, "К сожалению, ваша регистрация отклонена. Обратитесь к администратору.")
            bot.send_message(ADMIN_ID, f"Регистрация пользователя {fio} (ID: {user_id}) отклонена.")
        else:
            bot.send_message(ADMIN_ID, "Запрос на регистрацию с указанным ID не найден.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Произошла ошибка: {str(e)}")

# Глобальная переменная для хранения выбора пользователя
user_selections = {}


@bot.message_handler(func=lambda message: message.text == "Получить отчет")
def cmd_get_report(message):
    user_id = str(message.chat.id)
    logging.info(f"Запрос на выбор сетей от: {user_id}")
    if user_id in registration_data["registered"]:
        try:
            with open(FILE_PATHS_FILE, 'r', encoding='utf-8') as file:
                file_paths_data = json.load(file)
                available_networks = [entry["name"] for entry in file_paths_data.get("files", [])]
        except (FileNotFoundError, json.JSONDecodeError):
            bot.send_message(user_id, "Ошибка загрузки списка файлов. Проверьте файл file_paths.json.")
            return

        # Создаем клавиатуру с кнопками для выбора сетей
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        # Добавляем кнопки с учетом выбранных сетей
        for network in available_networks:
            # Если сеть выбрана, добавляем значок ✅
            if user_id in user_selections and network in user_selections[user_id].get("selected_networks", []):
                button_text = f"{network} ✅"
            else:
                button_text = network
            markup.add(types.KeyboardButton(button_text))

        markup.add(types.KeyboardButton("Готово"))

        bot.send_message(user_id, "Выберите сети магазинов для отчета:", reply_markup=markup)
        bot.register_next_step_handler(message, process_network_selection)
    else:
        bot.send_message(user_id, "Вы не зарегистрированы. Напишите /register для регистрации.")


def process_network_selection(message):
    user_id = str(message.chat.id)
    selected_network = message.text

    # Убираем значок ✅, если он есть
    selected_network = selected_network.replace(" ✅", "")
    if selected_network == '/reset':
        update_keyboard(user_id, "Бот успешно перезапущен!")
        return

    if selected_network == "Готово":
        finalize_report(user_id)  # Передаем user_id вместо call
        user_selections[user_id]["selected_networks"] = []
        return

    if user_id not in user_selections:
        user_selections[user_id] = {"selected_networks": []}

    if selected_network in user_selections[user_id]["selected_networks"]:
        user_selections[user_id]["selected_networks"].remove(selected_network)
        bot.send_message(user_id, f"Сеть {selected_network} убрана из выбора.")
    else:
        user_selections[user_id]["selected_networks"].append(selected_network)
        bot.send_message(user_id, f"Сеть {selected_network} добавлена в выбор.")

    # Повторно показываем клавиатуру для выбора
    cmd_get_report(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_network_selection(call):
    user_id = str(call.message.chat.id)
    if user_id not in user_selections:
        bot.send_message(user_id, "Что-то пошло не так. Попробуйте снова.")
        return

    network = call.data.replace("select_", "")
    if network == 'reset':
        update_keyboard(user_id, "Бот успешно перезапущен!")
        return
    if network == "done":
        finalize_report(user_id)  # Передаем user_id вместо call
        return

    if network in user_selections[user_id]["selected_networks"]:
        user_selections[user_id]["selected_networks"].remove(network)
        bot.answer_callback_query(call.id, f"Сеть {network} убрана из выбора.")
    else:
        user_selections[user_id]["selected_networks"].append(network)
        bot.answer_callback_query(call.id, f"Сеть {network} добавлена в выбор.")

    markup = types.InlineKeyboardMarkup()
    for network in user_selections[user_id]["available_networks"]:
        button_text = f"{network} {'✅' if network in user_selections[user_id]['selected_networks'] else ''}"
        button = types.InlineKeyboardButton(button_text, callback_data=f"select_{network}")
        markup.add(button)
    done_button = types.InlineKeyboardButton("Готово", callback_data="select_done")
    markup.add(done_button)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

def finalize_report(user_id):
    if user_id not in user_selections:
        bot.send_message(user_id, "Что-то пошло не так. Попробуйте снова.")
        return

    selected_networks = user_selections[user_id]["selected_networks"]

    if not selected_networks:
        bot.send_message(user_id, "Вы не выбрали ни одной сети. Попробуйте снова.")
        return

    try:
        with open(FILE_PATHS_FILE, 'r', encoding='utf-8') as file:
            file_paths_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        bot.send_message(user_id, "Ошибка загрузки списка файлов. Проверьте файл file_paths.json.")
        return

    file_paths = [
        entry["path"] for entry in file_paths_data.get("files", [])
        if entry["name"] in selected_networks
    ]

    if not file_paths:
        bot.send_message(user_id, "Не найдено файлов для выбранных сетей.")
        return

    bot.send_message(user_id, "Отчет создается...")
    update_keyboard(user_id, None)
    bot.send_chat_action(user_id, action='typing')
    results = process_excel_files(file_paths)
    if results:
        report_path = create_excel_report(results)
        with open(report_path, 'rb') as file:
            bot.send_document(user_id, file)
            logging.info(f"Отчет доставлен {user_id}")
        update_keyboard(user_id, "Отчет успешно отправлен.")
    else:
        update_keyboard(user_id, "Отчет успешно отправлен.")
        logging.info(f"Ошибок не выявлено {user_id}")


# Ключевые слова для фильтрации
keywords_baby = ["baby", "kids", "junior", "детский", "детей", "девочек", "мальчиков", "младенцев", "новорожд", "малышей",
                 "ребенок", "ребенка", "ребенку", "ребенком", "ребенке", "малыш", "малыша", "малышу", "малышом", "малыше",
                 "младенец", "младенца", "младенцу", "младенцем", "младенце", "новорожденный", "новорожденного",
                 "новорожденному", "новорожденным", "новорожденном", "детское", "детские", "дошкольник", "дошкольника",
                 "дошкольнику", "дошкольником", "дошкольнике", "школьник", "школьника", "школьнику", "школьником",
                 "школьнике", "подросток", "подростка", "подростку", "подростком", "подростке"]
# Категории по классификатору
categories = [
    "ORAL CARE прочее", "Антисептики", "Бальзамы для волос", "БАДы", "Влажн. салфетки Baby",
    "Гели для душа", "Влажн. туал. бумага", "Средства для купания Baby", "Дезодоранты",
    "Для пола (Поверхности)", "Для снятия макияжа", "Женская гигиена", "Жидкое мыло Home",
    "Жидкое мыло Beauty", "Жидкое мыло Baby", "Засоры", "Зубная паста", "Зубная паста Baby",
    "Зубные щетки", "Зубные щетки Baby", "Кондиционеры для белья", "Косметические и эфирные масла",
    "Кремы для детей", "Кремы для ног", "Кремы для рук и тела", "Кремы для лица", "Кухня (гель + крем)",
    "Кухня (спрей)", "Доп. уход за кожей ног", "Маски для волос", "Маски для лица",
    "Маски для лица тканевые", "Мицеллярные средства", "Твердое мыло Home", "Твердое мыло Beauty",
    "Твердое мыло Baby", "Наборы Oral", "НАБОРЫ Волосы", "Наборы Уход Baby", "НАБОРЫ Косметика",
    "Наборы Тело", "Наборы Красота Микс", "Наборы Стирка", "Наборы Уборка", "Окна",
    "Ополаскиватели д/рта", "Ополаскиватель + Соль + Очист. для Пмм", "Освежители воздуха",
    "Пены для ванны Baby", "Пены для ванны", "Пилинги для кожи головы", "Подгузники", "Посуда",
    "Посуда-Автомат (Гель + Порошок)", "Пятновыводитель + Отбеливатель",
    "Салфетки для стирки", "Салфетки для уборки", "Сантехника (Гель + Порошок)",
    "Сантехника (Спрей)", "Скрабы + Пилинги для лица", "Скрабы для тела", "Соль для ванны",
    "Доп. уход за кожей рук", "Тоники", "Средства для интимной гигиены", "Стирка (Жидкая)",
    "Стирка (Капсулы для стирки)", "Стирка (Стиральные порошки)", "Сыворотки для волос",
    "Сыворотки для лица", "Таблетки и капсулы для Пмм", "Универсальные средства",
    "Уход за кожей вокруг глаз", "Уход за проблемной кожей", "Шампуни", "Шампуни Baby",
    "Бальзамы для губ", "Наборы ПММ", "Доп. уход за волосами Baby", "Наборы Лицо"
]

def process_excel_files(file_paths):
    results = []
    logging.info("Начало создания отчета")
    for path in file_paths:
        if os.path.exists(path):
            try:
                df = pd.read_excel(path, sheet_name="SPR_DWH_SKU")
                required_columns = ["Код SKU", "Название SKU в сети", "Объем упаковки", "Бренд", "Уник. названия групп",
                                   "Линейка уровень 1", "Линейка уровень 2", "URL", "Код сети"]
                if all(col in df.columns for col in required_columns):
                    logging.info(f"Файл {path} успешно загружен и обработан.")
                    for _, row in df.iloc[:-1].iterrows():
                        unique_group = row["Уник. названия групп"]
                        if unique_group and isinstance(unique_group, str):
                            unique_group = unique_group.strip()
                            if unique_group != "Прочее":
                                try:
                                    # Флаг для проверки совпадения с категориями
                                    match_found = False
                                    # Проверяем, совпадает ли unique_group с какой-либо категорией
                                    for category in categories:
                                        if unique_group == category:
                                            match_found = True
                                            break  # Прерываем цикл, если найдено совпадение

                                    # Если совпадений не найдено, добавляем товар в результаты
                                    if not match_found:
                                        results.append({
                                            "sku_code": row["Код SKU"],
                                            "product_name": row["Название SKU в сети"],
                                            "volume": row["Объем упаковки"],
                                            "brand": None,
                                            "unique_group": unique_group,
                                            "line_1": row["Линейка уровень 1"],
                                            "line_2": row["Линейка уровень 2"],
                                            "url": row["URL"],
                                            "network_code": row["Код сети"],
                                            "file_path": path
                                        })

                                    product_name = row["Название SKU в сети"]
                                    if product_name and row["Линейка уровень 2"] != "Baby":
                                        product_name = product_name.lower()
                                        if any(keyword in product_name for keyword in keywords_baby):
                                            results.append({
                                                "sku_code": row["Код SKU"],
                                                "product_name": row["Название SKU в сети"],
                                                "volume": row["Объем упаковки"],
                                                "brand": None,
                                                "unique_group": None,
                                                "line_1": row["Линейка уровень 1"],
                                                "line_2": "Baby",
                                                "url": row["URL"],
                                                "network_code": row["Код сети"],
                                                "file_path": path
                                            })

                                    brand = row["Бренд"]
                                    if brand in ["Прочее", "Прочие", "0", "Нет бренда", "Без бренда",""] or not brand:
                                        results.append({
                                            "sku_code": row["Код SKU"],
                                            "product_name": row["Название SKU в сети"],
                                            "volume": row["Объем упаковки"],
                                            "brand": row["Бренд"],
                                            "unique_group": None,
                                            "line_1": row["Линейка уровень 1"],
                                            "line_2": None,
                                            "url": row["URL"],
                                            "network_code": row["Код сети"],
                                            "file_path": path
                                        })
                                except Exception as e:
                                        logging.error(f"Ошибка при обработке товара {row['Название SKU в сети']} в файле {path}: {str(e)}")
            except Exception as e:
                logging.error(f"Ошибка при обработке файла {path}: {str(e)}")
    logging.info(f"Создан отчет на базе: {file_paths}")
    return results


def create_excel_report(results):
    df = pd.DataFrame(results)  # Преобразуем результаты в DataFrame
    chunk_size = 1000000  # Количество строк на лист
    chunks = [df[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]  # Разбиваем DataFrame на чанки
    report_path = 'report.xlsx'  # Путь к файлу отчета

    # Запись в Excel-файл
    with pd.ExcelWriter(report_path) as writer:
        for i, chunk in enumerate(chunks):
            # Записываем каждый чанк на отдельный лист
            chunk.to_excel(writer, sheet_name=f'Sheet_{i + 1}', index=False)
    logging.info(f"Отчет успешно создан и сохранен в {report_path}.")
    return report_path  # Возвращаем путь к файлу

# Запуск бота
if __name__ == "__main__":
    logging.info("Бот запущен.")
    bot.infinity_polling()
