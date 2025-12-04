#!/usr/bin/env python3
"""
🤖 Telegram Bot - Собирает подписчиков в Google Sheets
✅ Работает через WEBHOOK (для серверов, включая BotHost)
✅ Отправляет данные в Google Sheets
✅ Отправляет промокод в приватный чат новому подписчику
"""

import logging
import gspread
import asyncio
import os
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, ChatMemberHandler, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask, request
import json

# ================== ЛОГИРОВАНИЕ ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== КОНФИГ ==================
BOT_TOKEN = os.getenv('BOT_TOKEN', '7904726862:AAFG3CurCeRels3tXl_agIYYzhn6vBNlk0c')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1001764760145'))
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44')
PROMO_POST_ID = int(os.getenv('PROMO_POST_ID', '42'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # Установлено в BotHost
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8080'))

# Google Sheets API
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

logger.info(f"📌 BOT_TOKEN: {BOT_TOKEN[:30]}...")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID[:30]}...")
logger.info(f"📌 WEBHOOK_URL: {WEBHOOK_URL}")

# ================== FLASK APP ==================
app = Flask(__name__)

# ================== GOOGLE SHEETS ==================
def get_gspread_client():
    """Получить клиент Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets клиент инициализирован")
        return client
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Google Sheets: {e}")
        return None

def log_subscriber_to_sheets(user_id: int, username: str = None) -> bool:
    """Добавить подписчика в Google Sheets"""
    try:
        client = get_gspread_client()
        if not client:
            logger.error("❌ Клиент Google Sheets недоступен")
            return False

        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        # Добавляем строку: [user_id, username, timestamp, status]
        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])

        logger.info(f"✅ Добавлен в таблицу: {user_id} (@{username})")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка добавления в Google Sheets: {e}")
        return False

# ================== TELEGRAM BOT HANDLERS ==================
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для отслеживания новых подписчиков"""
    try:
        logger.info("🔔 Обновление статуса члена чата получено")
        
        member_update = update.chat_member
        new_status = member_update.new_chat_member.status
        old_status = member_update.old_chat_member.status if member_update.old_chat_member else 'unknown'
        
        logger.info(f"Статус изменился: {old_status} → {new_status}")

        # Проверяем: это подписка? (переход из left/restricted в member)
        if new_status == 'member' and old_status in ['left', 'restricted', 'unknown', None]:
            user_id = member_update.new_chat_member.user.id
            username = member_update.new_chat_member.user.username
            first_name = member_update.new_chat_member.user.first_name

            logger.info(f"✅ НОВЫЙ ПОДПИСЧИК: {user_id} (@{username}) - {first_name}")

            # Логируем в Google Sheets
            if log_subscriber_to_sheets(user_id, username):
                logger.info(f"✅ {user_id} успешно добавлен в таблицу")
            else:
                logger.warning(f"⚠️ Не удалось добавить {user_id} в таблицу")

            # Отправляем приватное сообщение с промокодом
            try:
                keyboard = [[InlineKeyboardButton(
                    "🎁 Получить промокод на скидку",
                    url=f"https://t.me/senseandart/{PROMO_POST_ID}"
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 <b>Добро пожаловать!</b>\n\n"
                         "Спасибо что подписались на <b>@senseandart</b>!\n\n"
                         "👇 Нажмите кнопку и получите <b>промокод на скидку</b>:",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                logger.info(f"✅ Сообщение отправлено пользователю {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отправить сообщение {user_id}: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике chat_member: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name

        logger.info(f"📝 /start от {user_id} (@{username}) - {first_name}")

        # Проверяем подписку
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.warning(f"⚠️ Не удалось проверить подписку: {e}")
            is_member = False

        if is_member:
            # Уже подписан
            keyboard = [[InlineKeyboardButton(
                "🎁 Получить промокод на скидку",
                url=f"https://t.me/senseandart/{PROMO_POST_ID}"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
                "👇 Нажмите кнопку ниже:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # Не подписан
            keyboard = [[InlineKeyboardButton(
                "📢 Подписаться на канал @senseandart",
                url="https://t.me/senseandart"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Подпишитесь на канал <b>@senseandart</b> и получите <b>промокод на скидку</b>!\n\n"
                "После подписки я автоматически пришлю вам промокод 🎁\n\n"
                "👇 Нажмите кнопку ниже:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}")

# ================== WEBHOOK ROUTE ==================
@app.route('/webhook', methods=['POST'])
async def webhook():
    """Webhook для получения обновлений от Telegram"""
    try:
        data = request.get_json()
        logger.info(f"📨 Webhook получил данные: {json.dumps(data)[:200]}...")
        
        # Преобразуем в Update объект
        update = Update.de_json(data, application.bot)
        
        # Обрабатываем обновление
        await application.process_update(update)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}")
        return 'ERROR', 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья приложения"""
    return 'OK', 200

# ================== ГЛАВНАЯ ФУНКЦИЯ ==================
async def main():
    """Инициализация и запуск бота"""
    global application
    
    logger.info("🚀 Инициализация Application...")
    
    # Создаём Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    logger.info("📝 Добавляем обработчики...")
    
    # Обработчик для отслеживания новых подписчиков
    application.add_handler(ChatMemberHandler(
        handle_chat_member_update,
        ChatMemberHandler.CHAT_MEMBER
    ))
    
    # Обработчик для команды /start
    application.add_handler(CommandHandler("start", start_command))
    
    logger.info("✅ Обработчики добавлены")
    
    # Если есть WEBHOOK_URL, устанавливаем webhook
    if WEBHOOK_URL:
        logger.info(f"🔗 Устанавливаем webhook: {WEBHOOK_URL}")
        await application.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=['chat_member', 'message']
        )
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"✅ Webhook установлен: {webhook_info}")
    
    logger.info("✅ Бот готов к работе!")

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    import asyncio
    
    # Инициализируем бота
    asyncio.run(main())
    
    # Запускаем Flask (для webhook)
    logger.info(f"🌐 Запуск Flask сервера на порту {WEBHOOK_PORT}...")
    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False)
