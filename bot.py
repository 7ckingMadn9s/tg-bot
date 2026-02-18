import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime

TOKEN = "8033399130:AAGI_89YLNq-FBrD5CacJK0bBSqtC7hwSdc"
MAIN_ADMIN_ID = 804822685

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

DATA_DIR = '/app/data'
ADMINS_FILE = os.path.join(DATA_DIR, 'admins.json')
NEW_USERS_FILE = os.path.join(DATA_DIR, 'new_users.json')

app = Flask(__name__)
CORS(app)


def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as f:
            return json.load(f)
    return [MAIN_ADMIN_ID]


def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump(admins, f)


def load_new_users():
    if os.path.exists(NEW_USERS_FILE):
        with open(NEW_USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_new_users(users):
    with open(NEW_USERS_FILE, 'w') as f:
        json.dump(users, f)


def add_new_user(user_id, username):
    users = load_new_users()
    for user in users:
        if user['id'] == user_id:
            return False

    users.append({
        'id': user_id,
        'username': username,
        'date_added': str(datetime.now())
    })
    save_new_users(users)
    return True


def remove_new_user(user_id):
    users = load_new_users()
    users = [user for user in users if user['id'] != user_id]
    save_new_users(users)


def is_admin(user_id):
    admins = load_admins()
    return user_id in admins


def is_main_admin(user_id):
    return user_id == MAIN_ADMIN_ID


def get_user_username(user_id):
    try:
        user = bot.get_chat(user_id)
        if user.username:
            return f"@{user.username}"
        else:
            return "(нет username)"
    except:
        return "(скрыт или не найден)"


@app.route('/get_admins', methods=['GET'])
def get_admins_endpoint():
    admins = load_admins()
    print(f"Запрос списка админов: {admins}")
    return jsonify(admins)


@app.route('/send_application', methods=['POST'])
def send_application():
    try:
        data = request.json
        print(f"Получена заявка от backend: {data}")

        if 'ФИО' in data:
            message = f"""🔥 <b>НОВАЯ ЗАЯВКА С САЙТА</b> 🔥

<b>ФИО:</b> {data.get('ФИО', 'Не указано')}
<b>Телефон:</b> <code>{data.get('Телефон', 'Не указан')}</code>
<b>Комментарий:</b> {data.get('Комментарий', 'Не указан')}
<b>Дата/Время:</b> {data.get('Дата/Время', 'Не указано')}"""
        else:
            message = f"""🔥 <b>НОВАЯ ЗАЯВКА С САЙТА</b> 🔥

<b>Телефон:</b> <code>{data.get('Телефон', 'Не указан')}</code>
<b>Тип:</b> {data.get('Тип заявки', 'Обычная')}
<b>Дата/Время:</b> {data.get('Дата/Время', 'Не указано')}"""

        admins = load_admins()
        print(f"Отправка заявки администраторам: {admins}")

        success_count = 0
        for admin_id in admins:
            try:
                bot.send_message(admin_id, message, parse_mode='HTML')
                success_count += 1
                print(f"Заявка отправлена администратору {admin_id}")
            except Exception as e:
                print(f"Ошибка отправки администратору {admin_id}: {e}")

        return jsonify({
            "success": True,
            "message": f"Заявка отправлена {success_count} администраторам",
            "sent_count": success_count
        })

    except Exception as e:
        print(f"Ошибка обработки заявки: {e}")
        return jsonify({
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


def run_flask():
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)


def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("💻 Админ панель")
    markup.add(btn1)
    return markup


def get_admin_management_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("➕ Добавить администратора")
    btn2 = KeyboardButton("➖ Удалить администратора")
    btn3 = KeyboardButton("📋 Список администраторов")
    btn4 = KeyboardButton("↩ Назад")

    new_users = load_new_users()
    if new_users:
        btn_new = KeyboardButton(f"🆕 New ({len(new_users)})")
        markup.add(btn1, btn2, btn_new)
    else:
        markup.add(btn1, btn2)

    markup.add(btn3, btn4)
    return markup


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    username_display = f"@{username}" if username else "(нет username)"

    if is_admin(user_id):
        markup = get_admin_keyboard()
        bot.reply_to(
            message,
            "Вы являетесь администратором, теперь все заявки с сайта будут приходить к вам в чат ✅\n\nИспользуйте кнопки внизу для управления ⤵",
            reply_markup=markup
        )
    else:
        bot.reply_to(
            message,
            "Бот для получения заявок с сайта 🤖",
            reply_markup=ReplyKeyboardRemove()
        )

        if is_main_admin(MAIN_ADMIN_ID):
            users = load_new_users()
            user_exists = False
            for user in users:
                if user['id'] == user_id:
                    user_exists = True
                    break

            if not user_exists:
                users.append({
                    'id': user_id,
                    'username': username_display,
                    'date_added': str(datetime.now())
                })
                save_new_users(users)

                try:
                    admin_markup = get_admin_management_keyboard()
                    bot.send_message(
                        MAIN_ADMIN_ID,
                        f"🆕 Новый пользователь активировал бота:\n\nID: {user_id}\nUsername: {username_display}",
                        reply_markup=admin_markup
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления главному админу: {e}")


@bot.message_handler(func=lambda message: message.text and "🆕 New" in message.text)
def show_new_users(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    new_users = load_new_users()
    if not new_users:
        bot.send_message(message.chat.id, "Новых пользователей нет")
        return

    user_list = []
    for user in new_users:
        user_list.append(f"ID: {user['id']}\nUsername: {user['username']}")

    markup = get_admin_management_keyboard()
    bot.send_message(
        message.chat.id,
        f"🆕 Новые пользователи:\n\n" + "\n\n".join(user_list),
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "💻 Админ панель")
def admin_management(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для управления администраторами")
        return

    markup = get_admin_management_keyboard()
    bot.send_message(
        message.chat.id,
        "Управление администраторами\n\nВыберите действие:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "↩ Назад")
def back_to_main(message):
    if is_admin(message.from_user.id):
        markup = get_admin_keyboard()
        bot.send_message(
            message.chat.id,
            "Вы являетесь администратором, теперь все заявки с сайта будут приходить к вам в чат ✅\n\nИспользуйте кнопки внизу для управления ⤵",
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: message.text == "➕ Добавить администратора")
def add_admin_request(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    cancel_btn = KeyboardButton("❌ Отмена")
    markup.add(cancel_btn)

    bot.send_message(
        message.chat.id,
        "➕ Добавление администратора\n\nВведите Telegram ID пользователя, которого хотите добавить:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, process_add_admin)


@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def cancel_action(message):
    admin_management(message)


@bot.message_handler(func=lambda message: message.text == "➖ Удалить администратора")
def remove_admin_request(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    admins = load_admins()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    for admin_id in admins:
        if admin_id != MAIN_ADMIN_ID:
            username = get_user_username(admin_id)
            btn_text = f"❌ Удалить {admin_id} {username}"
            markup.add(KeyboardButton(btn_text))

    cancel_btn = KeyboardButton("↩ Назад")
    markup.add(cancel_btn)

    bot.send_message(
        message.chat.id,
        "➖ Удаление администратора\n\nВыберите администратора для удаления:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text and message.text.startswith("❌ Удалить "))
def process_remove_admin(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    try:
        parts = message.text.split()
        user_id = int(parts[2])
        username = parts[3] if len(parts) > 3 else "(нет username)"

        admins = load_admins()

        if user_id == MAIN_ADMIN_ID:
            bot.reply_to(message, "❌ Нельзя удалить главного администратора")
        elif user_id in admins:
            admins.remove(user_id)
            save_admins(admins)
            bot.reply_to(message, f"✅ Пользователь {user_id} {username} удален из администраторов")
            print(f"Администратор {user_id} удален. Текущий список: {admins}")
        else:
            bot.reply_to(message, f"❌ Пользователь {user_id} не является администратором")

        remove_admin_request(message)

    except (ValueError, IndexError):
        bot.reply_to(message, "❌ Ошибка при удалении администратора")


@bot.message_handler(func=lambda message: message.text == "📋 Список администраторов")
def list_admins(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    admins = load_admins()
    admin_lines = []

    for admin_id in admins:
        username = get_user_username(admin_id)
        if admin_id == MAIN_ADMIN_ID:
            admin_lines.append(f"{admin_id} {username} (главный)")
        else:
            admin_lines.append(f"{admin_id} {username}")

    admin_list = "\n".join(admin_lines)
    markup = get_admin_management_keyboard()

    bot.send_message(
        message.chat.id,
        f"📋 Список администраторов:\n\n{admin_list}",
        reply_markup=markup
    )


def process_add_admin(message):
    if message.text == "❌ Отмена":
        admin_management(message)
        return

    try:
        user_id = int(message.text.strip())
        admins = load_admins()

        if user_id in admins:
            bot.reply_to(message, f"❌ Пользователь {user_id} уже является администратором")
        else:
            # ✅ ИСПРАВЛЕНИЕ: Добавляем пользователя в список администраторов
            admins.append(user_id)
            save_admins(admins)

            username = get_user_username(user_id)
            bot.reply_to(message, f"✅ Пользователь {user_id} {username} добавлен в администраторы")
            print(f"Администратор {user_id} добавлен. Текущий список: {admins}")

            remove_new_user(user_id)

            main_admin_username = get_user_username(MAIN_ADMIN_ID)

            try:
                # ✅ ИСПРАВЛЕНИЕ: Отправляем приветственное сообщение новому администратору
                markup = get_admin_keyboard()
                bot.send_message(
                    user_id,
                    f"Главный администратор {main_admin_username} добавил вас в администраторы ‼\n\n"
                    f"Вы являетесь администратором, теперь все заявки с сайта будут приходить к вам в чат ✅\n\n"
                    f"Используйте кнопки внизу для управления ⤵",
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

        admin_management(message)

    except ValueError:
        bot.reply_to(message, "❌ Ошибка: введите корректный Telegram ID (только цифры)")
        admin_management(message)


@bot.message_handler(commands=['add_admin'])
def add_admin_command(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    try:
        user_id = int(message.text.split()[1])
        admins = load_admins()

        if user_id in admins:
            bot.reply_to(message, f"Пользователь {user_id} уже является администратором")
        else:
            # ✅ ИСПРАВЛЕНИЕ: Добавляем пользователя в список администраторов
            admins.append(user_id)
            save_admins(admins)

            username = get_user_username(user_id)
            bot.reply_to(message, f"Пользователь {user_id} {username} добавлен в администраторы")
            print(f"Администратор {user_id} добавлен. Текущий список: {admins}")

            remove_new_user(user_id)

            main_admin_username = get_user_username(MAIN_ADMIN_ID)

            try:
                # ✅ ИСПРАВЛЕНИЕ: Отправляем приветственное сообщение новому администратору
                markup = get_admin_keyboard()
                bot.send_message(
                    user_id,
                    f"Главный администратор {main_admin_username} добавил вас в администраторы ‼\n\n"
                    f"Вы являетесь администратором, теперь все заявки с сайта будут приходить к вам в чат ✅\n\n"
                    f"Используйте кнопки внизу для управления ⤵",
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

    except (IndexError, ValueError):
        bot.reply_to(message, "Использование: /add_admin TELEGRAM_ID")


@bot.message_handler(commands=['remove_admin'])
def remove_admin_command(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    try:
        user_id = int(message.text.split()[1])
        admins = load_admins()

        if user_id == MAIN_ADMIN_ID:
            bot.reply_to(message, "Нельзя удалить главного администратора")
        elif user_id in admins:
            admins.remove(user_id)
            save_admins(admins)

            username = get_user_username(user_id)
            bot.reply_to(message, f"Пользователь {user_id} {username} удален из администраторов")
            print(f"Администратор {user_id} удален. Текущий список: {admins}")
        else:
            bot.reply_to(message, f"Пользователь {user_id} не является администратором")

    except (IndexError, ValueError):
        bot.reply_to(message, "Использование: /remove_admin TELEGRAM_ID")


@bot.message_handler(commands=['list_admins'])
def list_admins_command(message):
    if not is_main_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для этой команды")
        return

    admins = load_admins()
    admin_lines = []

    for admin_id in admins:
        username = get_user_username(admin_id)
        if admin_id == MAIN_ADMIN_ID:
            admin_lines.append(f"{admin_id} {username} (главный)")
        else:
            admin_lines.append(f"{admin_id} {username}")

    admin_list = "\n".join(admin_lines)
    bot.reply_to(message, f"Список администраторов:\n{admin_list}")


if __name__ == '__main__':
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("Бот успешно запущен")
    print(f"Flask сервер запущен на порту 5001")
    print(f"Текущий список администраторов: {load_admins()}")
    print("✅ Эндпоинт /send_application доступен для получения заявок")
    bot.polling(none_stop=True)