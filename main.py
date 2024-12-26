import telebot
from telebot import types
import datetime
import json
import os

API_TOKEN = '7231631738:AAGb0c7UzDDO5sAyjnJANLuwHMB1yPNVo1c'
bot = telebot.TeleBot(API_TOKEN)

# Файл для хранения событий
data_file = 'events.json'

# Загрузка событий из файла
def load_events():
    if os.path.exists(data_file):  # Проверка существования файла
        with open(data_file, 'r') as f:
            return json.load(f)  # Загрузка данных из файла JSON
    return {}  # Возврат пустого словаря, если файл не найден

# Сохранение событий в файл
def save_events(events):
    with open(data_file, 'w') as f:
        json.dump(events, f, indent=4)  # Запись данных в JSON-файл с отступами

# Инициализация событий
user_events = load_events()

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот-планировщик. Давайте начнем планировать ваш день!\nИспользуйте команды: /add, /view, /edit, /delete.")

# Обработка команды /add для добавления события
@bot.message_handler(commands=['add'])
def add_event(message):
    msg = bot.send_message(message.chat.id, "Введите событие в формате: Название, Дата(YYYY-MM-DD), Время(HH:MM)")
    bot.register_next_step_handler(msg, process_event)  # Ожидание следующего сообщения от пользователя

# Обработка добавления события
def process_event(message):
    try:
        event_data = message.text.split(',')  # Разделение текста по запятым
        name, date, time = event_data[0].strip(), event_data[1].strip(), event_data[2].strip()
        
        # Проверка формата даты и времени
        datetime.datetime.strptime(date, '%Y-%m-%d')
        datetime.datetime.strptime(time, '%H:%M')

        user_id = str(message.chat.id)  # Получение ID пользователя
        
        # Создание списка событий для пользователя, если он еще не существует
        if user_id not in user_events:
            user_events[user_id] = []
        
        # Добавление нового события
        user_events[user_id].append({'name': name, 'date': date, 'time': time})
        save_events(user_events)  # Сохранение событий в файл
        bot.send_message(message.chat.id, f'Событие "{name}" добавлено на {date} в {time}.')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка в формате данных. Пожалуйста, введите событие снова.')

# Обработка команды /view для просмотра событий
@bot.message_handler(commands=['view'])
def view_events(message):
    user_id = str(message.chat.id)
    if user_id in user_events and user_events[user_id]:  # Проверка наличия событий у пользователя
        events_list = '\n'.join([f'{e["name"]} - {e["date"]} {e["time"]}' for e in user_events[user_id]])
        bot.send_message(message.chat.id, f'Ваши события:\n{events_list}')
    else:
        bot.send_message(message.chat.id, 'У вас нет запланированных событий.')

# Обработка команды /delete для удаления событий
@bot.message_handler(commands=['delete'])
def delete_event(message):
    user_id = str(message.chat.id)
    if user_id in user_events and user_events[user_id]:  # Проверка наличия событий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)  
        for event in user_events[user_id]:
            markup.add(event['name'])
        msg = bot.send_message(message.chat.id, 'Выберите событие для удаления:', reply_markup=markup)
        bot.register_next_step_handler(msg, process_delete_event)  # Ожидание выбора события
    else:
        bot.send_message(message.chat.id, 'Удалять нечего.')

# Обработка удаления события
def process_delete_event(message):
    user_id = str(message.chat.id)
    event_name = message.text
    
    # Удаление события из списка
    user_events[user_id] = [e for e in user_events[user_id] if e['name'] != event_name]
    save_events(user_events)  # Сохранение изменений
    bot.send_message(message.chat.id, f'Событие "{event_name}" удалено.')

# Обработка команды /edit для редактирования событий
@bot.message_handler(commands=['edit'])
def edit_event(message):
    user_id = str(message.chat.id)
    if user_id in user_events and user_events[user_id]:  # Проверка наличия событий
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # Клавиатура с выбором событий
        for event in user_events[user_id]:
            markup.add(event['name'])
        msg = bot.send_message(message.chat.id, 'Выберите событие для редактирования:', reply_markup=markup)
        bot.register_next_step_handler(msg, process_edit_event)
    else:
        bot.send_message(message.chat.id, 'Редактировать нечего.')

# Обработка редактирования события
def process_edit_event(message):
    user_id = str(message.chat.id)
    event_name = message.text
    
    for event in user_events[user_id]:
        if event['name'] == event_name:
            msg = bot.send_message(message.chat.id, 'Введите новое событие в формате: Название, Дата(YYYY-MM-DD), Время(HH:MM)')
            bot.register_next_step_handler(msg, lambda msg: update_event(msg, event))
            return
    bot.send_message(message.chat.id, 'Событие не найдено.')

# Обновление события
def update_event(message, event):
    try:
        event_data = message.text.split(',')
        name, date, time = event_data[0].strip(), event_data[1].strip(), event_data[2].strip()
        datetime.datetime.strptime(date, '%Y-%m-%d')
        datetime.datetime.strptime(time, '%H:%M')

        event.update({'name': name, 'date': date, 'time': time})
        save_events(user_events)
        bot.send_message(message.chat.id, f'Событие обновлено: {name} - {date} {time}')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка в формате данных. Попробуйте снова.')

# Обработка неизвестных команд
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, 'Извините, я не понял команду. Пожалуйста, используйте /start для начала работы.')

# Запуск бота
bot.polling()
