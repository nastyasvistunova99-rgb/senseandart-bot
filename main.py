#!/usr/bin/env python3
"""
Telegram Bot for collecting new channel subscribers into Google Sheets
"""

import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003027665711'))
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44')
SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')
PROMO_POST_ID = int(os.getenv('PROMO_POST_ID', '42'))
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

logger.info(f"📌 BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID[:20]}...")

# Кэш уже добавленных пользователей
added_users = set()


def get_gspread_client():
    """Get gspread client for Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets client connected!")
        return client
    except Exception as e:
        logger.error(f"❌ ERROR loading credentials: {e}")
        return None


def log_subscriber(user_id: int, username: str = None):
    """Log subscriber to Google Sheets"""
    try:
        # Пропускаем если уже добавлен
        if user_id in added_users:
            logger.info(f"⚠️ User {user_id} already in cache, skipping")
            return True

        logger.info(f"📝 Attempting to log user {user_id}...")

        client = get_gspread_client()
        if not client:
            logger.error("❌ Google Sheets client is None!")
            return False

        # Открываем таблицу
        logger.info(f"📂 Opening spreadsheet: {GOOGLE_SHEETS_ID}")
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        logger.info(f"📊 Worksheet opened: {worksheet.title}")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        logger.info(f"📥 Adding row: [{user_id}, {username_str}, {timestamp}, subscribed]")
        
        # Добавляем строку
        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])

        # Добавляем в кэш
        added_users.add(user_id)

        logger.info(f"✅✅✅ SUCCESSFULLY ADDED TO SHEET: {user_id} (@{username})")
        return True

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR logging to Google Sheets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    first_name = update.effective_user.first_name or "Friend"

    logger.info(f"🎯🎯🎯 /START COMMAND from {user_id} (@{username})")

    # Логируем в таблицу СРАЗУ
    logger.info(f"📝 Logging subscriber: {user_id}")
    logged = log_subscriber(user_id, username)
    
    if logged:
        logger.info(f"✅ Successfully logged {user_id}")
    else:
        logger.error(f"❌ Failed to log {user_id}")

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
        "👇 Нажмите кнопку ниже и получите <b>промокод на скидку</b>:"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"✅ Message sent to {user_id}")


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    text = update.message.text

    logger.info(f"📨 MESSAGE from {user_id} (@{username}): {text}")

    # Логируем в таблицу СРАЗУ
    logger.info(f"📝 Logging subscriber from message: {user_id}")
    logged = log_subscriber(user_id, username)
    
    if logged:
        logger.info(f"✅ Successfully logged {user_id}")
    else:
        logger.error(f"❌ Failed to log {user_id}")

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
        "👇 Нажмите кнопку ниже и получите <b>промокод на скидку</b>:"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"✅ Message sent to {user_id}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"❌ ERROR: {context.error}")
    import traceback
    logger.error(traceback.format_exc())


def main():
    """Start the bot"""
    logger.info("🚀🚀🚀 STARTING BOT...")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add /start command handler
    application.add_handler(CommandHandler("start", start))

    # Add any message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("✅✅✅ BOT IS RUNNING...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
