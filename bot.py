import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import json

# ================= НАСТРОЙКИ =================
TOKEN = os.environ.get("8382305639:AAEZVv9XWu4TZZhL_HWfeIUTat9Wx5uLm7w")
if not TOKEN:
    raise RuntimeError("8382305639:AAEZVv9XWu4TZZhL_HWfeIUTat9Wx5uLm7w")

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"

# ================= ВСЕ ПЕРСОНАЖИ GACHIAKUTA =================
DEFAULT_ROLES = {
    # Чистильщики
    "Рудо": None,
    "Энзин": None,
    "Заби": None,
    "Риё": None,
    "Семиу": None,
    "Гитар": None,
    "Теру": None,
    "Занка Нидзику": None,

    # Обитатели Ямы
    "Амо": None,
    "Джаббер": None,
    "Ноит": None,
    "Регто": None,
    "Корубун": None,
    "Фу": None,

    # Фигуры влияния
    "Канцер": None,
    "Чил": None,
    "Грем": None,
    "Мэр Ямы": None,
    "Старейшина Ямы": None
}

# ================= ДАННЫЕ =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"roles": DEFAULT_ROLES, "stats": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📋 Роли", "📊 Моя статистика", "🧹 Доложить об уборке")

    bot.send_message(
        message.chat.id,
        f"ШТАБ GACHIAKUTA АКТИВЕН\n"
        f"Боец: {message.from_user.first_name}\n\n"
        "Выберите действие.",
        reply_markup=kb
    )

# ================= ОСНОВА =================
@bot.message_handler(content_types=["text"])
def handle_message(message):
    uid = str(message.from_user.id)
    data["stats"][uid] = data["stats"].get(uid, 0) + 1
    save_data()

    if message.text == "📋 Роли":
        show_roles(message)

    elif message.text == "📊 Моя статистика":
        count = data["stats"].get(uid, 0)
        rank = "Новобранец" if count < 100 else "Опытный Чистильщик"
        bot.send_message(
            message.chat.id,
            f"Статистика бойца:\n"
            f"Сообщений: {count}\n"
            f"Ранг: {rank}"
        )

    elif message.text == "🧹 Доложить об уборке":
        bot.send_message(message.chat.id, "Рапорт принят.")

# ================= РОЛИ =================
def show_roles(message):
    text = "ПЕРСОНАЖИ GACHIAKUTA:\n\n"
    markup = types.InlineKeyboardMarkup()
    buttons = []
    uid = str(message.from_user.id)
    user_role = None

    for role, owner in data["roles"].items():
        if owner:
            try:
                member = bot.get_chat_member(message.chat.id, int(owner))
                name = member.user.first_name
            except:
                name = "Неизвестен"
            text += f"👤 {role} — {name}\n"
            if owner == uid:
                user_role = role
        else:
            text += f"▫️ {role} — свободно\n"
            buttons.append(
                types.InlineKeyboardButton(
                    text=f"Взять {role}",
                    callback_data=f"take_{role}"
                )
            )

    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i + 2])

    if user_role:
        markup.row(
            types.InlineKeyboardButton(
                text="❌ Снять мою роль",
                callback_data="drop_role"
            )
        )

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("take_"))
def take_role(call):
    role = call.data.replace("take_", "")
    uid = str(call.from_user.id)

    if uid in data["roles"].values():
        bot.answer_callback_query(call.id, "У вас уже есть роль")
        return

    if data["roles"].get(role) is None:
        data["roles"][role] = uid
        save_data()
        bot.send_message(
            call.message.chat.id,
            f"{call.from_user.first_name} назначен на роль: {role}"
        )
        bot.answer_callback_query(call.id, "Роль получена")
    else:
        bot.answer_callback_query(call.id, "Роль занята")

@bot.callback_query_handler(func=lambda call: call.data == "drop_role")
def drop_role(call):
    uid = str(call.from_user.id)
    for role, owner in data["roles"].items():
        if owner == uid:
            data["roles"][role] = None
            save_data()
            bot.send_message(
                call.message.chat.id,
                f"Роль {role} снята."
            )
            bot.answer_callback_query(call.id, "Роль снята")
            return
    bot.answer_callback_query(call.id, "У вас нет роли")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Gachiakuta HQ ONLINE"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

# ================= ЗАПУСК =================
if __name__ == "__main__":
    keep_alive()
    print("Gachiakuta bot running")
    bot.polling(non_stop=True)
