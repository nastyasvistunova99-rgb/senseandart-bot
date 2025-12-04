#!/usr/bin/env python3
"""
🤖 Простой Telegram Bot с POLLING
✅ Собирает подписчиков в Google Sheets
✅ Отправляет промокод в приватный чат
"""

import logging
import gspread
import os
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, ChatMemberHandler, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials

# ================== ЛОГИРОВАНИЕ ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== ПАРАМЕТРЫ ==================
BOT_TOKEN = "7904726862:AAFG3CurCeRels3tXl_agIYYzhn6vBNlk0c"
CHANNEL_ID = -1001764760145
GOOGLE_SHEETS_ID = "18RwlO7h0R6FF8xOthOrIDyOvpfjP7doXcJ1fOcJu-2g"
PROMO_POST_ID = 42
CREDENTIALS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

logger.info("=" * 50)
logger.info(f"📌 BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID[:20]}...")
logger.info("=" * 50)

# ================== GOOGLE SHEETS ==================
def get_gspread_client():
    """Получить клиент Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets клиент готов")
        return client
    except Exception as e:
        logger.error(f"❌ Ошибка Google Sheets: {e}")
        return None

def log_subscriber(user_id: int, username: str = None) -> bool:
    """Добавить подписчика в таблицу"""
    try:
        client = get_gspread_client()
        if not client:
            return False

        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])
        logger.info(f"✅ Добавлен: {user_id} (@{username})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка добавления: {e}")
        return False

# ================== ОБРАБОТЧИКИ ==================
async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживание новых подписчиков"""
    try:
        member_update = update.chat_member
        new_status = member_update.new_chat_member.status
        old_status = member_update.old_chat_member.status if member_update.old_chat_member else None

        if new_status == 'member' and old_status in ['left', 'restricted', None]:
            user_id = member_update.new_chat_member.user.id
            username = member_update.new_chat_member.user.username
            first_name = member_update.new_chat_member.user.first_name

            logger.info(f"✅ НОВЫЙ ПОДПИСЧИК: {user_id} (@{username}) - {first_name}")

            # Логируем в Google Sheets
            log_subscriber(user_id, username)

            # Отправляем приватное сообщение
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
                logger.info(f"✅ Сообщение отправлено {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка отправки: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка обработчика: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        logger.info(f"📝 /start от {user_id} (@{username})")

        # Проверяем подписку
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
        except:
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
            # Не подписан - просим подписаться
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
        logger.error(f"❌ Ошибка /start: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка: {context.error}")

# ================== ГЛАВНАЯ ФУНКЦИЯ ==================
def main():
    """Запуск бота"""
    logger.info("🚀 Инициализация Application...")

    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    logger.info("📝 Добавляем обработчики...")
    
    application.add_handler(ChatMemberHandler(
        handle_chat_member,
        ChatMemberHandler.CHAT_MEMBER
    ))
    application.add_handler(CommandHandler("start", start_command))
    application.add_error_handler(error_handler)

    logger.info("✅ Обработчики добавлены")
    logger.info("🔄 Запускаем POLLING...")

    # Запускаем бота
    application.run_polling(timeout=30, allowed_updates=['chat_member', 'message'])

if __name__ == '__main__':
    main()
