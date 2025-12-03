#!/usr/bin/env python3
"""
Telegram Bot - записывает пользователей в Google Sheets
"""

import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ЖЁСТКИЕ ЗНАЧЕНИЯ ==========
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
CHANNEL_ID = -1003027665711
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
PROMO_POST_ID = 42
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# =====================================

logger.info("=" * 60)
logger.info("🚀 БОТ ЗАПУСКАЕТСЯ")
logger.info(f"📌 BOT_TOKEN: {BOT_TOKEN[:25]}...")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID[:30]}...")
logger.info(f"📌 CREDENTIALS_FILE: {CREDENTIALS_FILE}")
logger.info("=" * 60)

added_users = set()


def get_gspread_client():
    """Подключение к Google Sheets"""
    try:
        logger.info(f"🔑 Загружаю credentials из: {CREDENTIALS_FILE}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, SCOPES)
        logger.info("✅ Credentials загружены успешно!")
        
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets client авторизован!")
        return client
        
    except FileNotFoundError:
        logger.error(f"❌ ФАЙЛ НЕ НАЙДЕН: {CREDENTIALS_FILE}")
        return None
    except Exception as e:
        logger.error(f"❌ ОШИБКА подключения: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def log_subscriber(user_id: int, username: str = None):
    """Добавляем пользователя в Google Sheets"""
    try:
        if user_id in added_users:
            logger.info(f"⏭️ User {user_id} уже добавлен, пропускаю")
            return True

        logger.info(f"\n📝 ДОБАВЛЯЮ ПОЛЬЗОВАТЕЛЯ: {user_id} (@{username})")

        client = get_gspread_client()
        if not client:
            logger.error("❌ Google Sheets client is None!")
            return False

        logger.info(f"📂 Открываю таблицу...")
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        logger.info(f"✅ Таблица открыта: {spreadsheet.title}")
        
        worksheet = spreadsheet.sheet1
        logger.info(f"✅ Лист открыт: {worksheet.title}")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        row_data = [str(user_id), username_str, timestamp, 'subscribed']
        logger.info(f"📥 Добавляю строку: {row_data}")
        
        worksheet.append_row(row_data)
        logger.info(f"✅ Строка добавлена!")

        added_users.add(user_id)

        logger.info(f"🎉 УСПЕХ! Пользователь {user_id} (@{username}) добавлен в таблицу!\n")
        return True

    except Exception as e:
        logger.error(f"❌ ОШИБКА при добавлении: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    first_name = update.effective_user.first_name or "Friend"

    logger.info(f"🎯 /START команда от {user_id} (@{username})")

    # Логируем в таблицу
    log_subscriber(user_id, username)

    # Отправляем промокод
    keyboard = [
        [InlineKeyboardButton(
            "🎁 Получить промокод на скидку",
            url=f"https://t.me/senseandart/{PROMO_POST_ID}"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        f"🎉 <b>Привет, {first_name}!</b>\n\n"
        "Спасибо что подписались на <b>@senseandart</b>!\n\n"
        "👇 Нажмите кнопку и получите <b>промокод на скидку</b>:"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"✅ Сообщение отправлено {user_id}\n")


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    text = update.message.text

    logger.info(f"📨 СООБЩЕНИЕ от {user_id}: {text}")

    # Логируем в таблицу
    log_subscriber(user_id, username)

    # Отправляем промокод
    keyboard = [
        [InlineKeyboardButton(
            "🎁 Получить промокод на скидку",
            url=f"https://t.me/senseandart/{PROMO_POST_ID}"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
        "👇 Нажмите кнопку и получите <b>промокод на скидку</b>:"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"✅ Сообщение отправлено {user_id}\n")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"❌ ОШИБКА: {context.error}")
    import traceback
    logger.error(traceback.format_exc())


def main():
    """Запуск бота"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀🚀🚀 ЗАПУСКАЮ БОТ...")
    logger.info("=" * 60 + "\n")

    application = Application.builder().token(BOT_TOKEN).build()

    # Хэндлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    application.add_error_handler(error_handler)

    # Запуск
    logger.info("✅✅✅ БОТ ГОТОВ К РАБОТЕ!")
    logger.info("=" * 60 + "\n")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
