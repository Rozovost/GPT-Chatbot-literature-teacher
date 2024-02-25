import telebot
import json
import logging as log
from config import bot_token
from gpt import get_resp
from telebot.types import ReplyKeyboardMarkup
bot = telebot.TeleBot(bot_token)  # Введите свой токен в config.py
continue_array = ["continue", "contunie", "con", "cont", "продолжить", "продолжит"]

# log конфиг
log.basicConfig(
    level=log.INFO,
    filemode="w",
    filename="logbook.txt",
    format='%(asctime)s - %(levelname)s - %(message)s')


# сбор стандартной клавиатуры
keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
keyboard.add("/solve_task")
keyboard.add("/continue")
keyboard.add("/stats")
keyboard.add("/help")

# сбор клавиатуры для continue
cont_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cont_keyboard.add("/solve_task")
cont_keyboard.add("/continue")
cont_keyboard.add("/stats")
cont_keyboard.add("/help")
cont_keyboard.add("/response")

# сбор клавиатуры старта
start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
start_keyboard.add("/help")

data_file = open('users_data.json', 'r', encoding='utf8')
try:  # попытка загрузки файла
    users_data = {}
    temp_file = json.load(data_file)
    for i in temp_file:  # преобразование формата
        temp_id = int(i)
        users_data[temp_id] = {}
        for e in temp_file[i]:
            users_data[temp_id][e] = temp_file[i][e]
    log.info("Файл загружен")
except:
    users_data = {}
    log.info("Ошибка загрузки файла")
data_file.close()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    reg(message)
    bot.send_message(message.chat.id, f"Привет, {users_data[user_id]['name']}! Я GPT бот-помощник, "
                                      f"имитирующий учителя литературы!\n"
                                      "Я могу рассказать вам о любом литературном герое.\n" # дополнить
                                      "Введите /help, чтобы получить список моих команд.\n",
                     reply_markup=start_keyboard)
    return


# Прием и обработка промтов


@bot.message_handler(commands=['solve_task'])
def solve_task_message(message):
    bot.send_message(message.chat.id, "Введите ваш вопрос.")
    bot.register_next_step_handler(message, get_promt)
    return


def get_promt(message):  # получение промта и его проверка
    user_id = message.from_user.id
    users_data[user_id]['prev_answer'] = ""
    if message.content_type == 'text':
        if message.text[0] != '/':
            promt = message.text
            log.info("promt received")
            log.info(f'{users_data[user_id]["name"]}: {promt}')
            users_data[user_id]['promts_count'] += 1
            users_data[user_id]['promt'] = promt
            data_save()
            answer_to_promt(promt, message.chat.id, user_id, keyboard)
        else:
            bot.send_message(message.chat.id, "В данный момент команды недоступны.\n"
                                              "Введите вопрос.")
            bot.register_next_step_handler(message, get_promt)
    else:
        bot.send_message(message.chat.id, "Отправьте вопрос текстом.")
        bot.register_next_step_handler(message, get_promt)
    return


def answer_to_promt(promt, chat_id, user_id, answer_keyboard):  # ответ на промт
    answer = get_resp(promt, users_data[user_id]['prev_answer'])
    if answer != "ERROR":
        if answer != "":
            users_data[user_id]['prev_answer'] += " " + answer
            bot.send_message(chat_id, answer)
            bot.send_message(chat_id, "Чтобы продолжить ответ, напиши /continue", reply_markup=answer_keyboard)
        else:
            bot.send_message(chat_id, "Мне больше нечего добавить.\n"
                                      "Введите /response, чтобы увидеть полный ответ.", reply_markup=cont_keyboard)
        log.info("response received")
    else:
        bot.send_message(chat_id, "При генерации ответа на промт произошла ошибка. Попробуйте ещё раз.",
                         reply_markup=keyboard)
        log.error("No response received")
    data_save()
    return

####################


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Введите /solve_task, чтобы задать вопрос.\n"
                                      "Введите /continue, чтобы бот продолжил свой ответ.\n"
                                      "Введите /stats, чтобы узнать сколько раз вы задали вопрос.\n"
                                      "Введите /response, чтобы просуммировать ответ бота на заданный вопрос "
                                      "(совмещает все ответы бота в один после команды continue).",
                     reply_markup=keyboard)
    return


@bot.message_handler(commands=continue_array)  # продолжить ответ
def continue_message(message):
    user_id = message.from_user.id
    if users_data[user_id]['promt'] != "":
        bot.send_message(message.chat.id, "Продолжаю...")
        answer_to_promt(users_data[user_id]['promt'], message.chat.id, user_id, cont_keyboard)
    else:
        bot.send_message(message.chat.id, "Сначала вам нужно задать вопрос.")
    return


@bot.message_handler(commands=['debug'])  # Дебаг
def debug_message(message):
    bot.send_message(message.chat.id, "Отправляю логбук:")
    with open("logbook.txt", "rb") as f:
        bot.send_document(message.chat.id, f)
    return


@bot.message_handler(commands=['response'])  # Показывает полный ответ
def show_complete_response(message):
    user_id = message.from_user.id
    if users_data[user_id]['prev_answer'] != '':
        bot.send_message(message.chat.id, f"Суммирую ответ:\n"
                                          f"{users_data[user_id]['prev_answer']}")
    else:
        bot.send_message(message.chat.id, "Ответ пуст. Попробуйте задать вопрос.")
    return


@bot.message_handler(commands=['stats'])  # Показывает сколько раз пользователь задал вопрос
def debug_message(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Вы задали вопрос {users_data[user_id]['promts_count']} раз.")
    return


@bot.message_handler(content_types=['text'])  # Обработка текста
def answer_to_text(message):
    bot.send_message(message.chat.id, "Выберите одну из предложенных команд", reply_markup=keyboard)
    return


def reg(message):  # Регистрация
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {}
        users_data[user_id]['name'] = message.from_user.first_name
        users_data[user_id]['promt'] = ""
        users_data[user_id]['promts_count'] = 0
        log.info(f"{users_data[user_id]['name']} зарегистрирован")
        log.info(users_data)
        data_save()
    else:
        log.info("Пользователь уже зарегистрирован")
    return


def data_save():  # Сохранение данных
    with open('users_data.json', 'w', encoding='utf8') as data:
        json.dump(users_data, data, indent=2, ensure_ascii=False)
        data.close()
    return


log.info("Бот запущен")
log.info(users_data)
bot.polling(non_stop=True)
