#!/usr/bin/env python3
"""
Telegram Bot for collecting new channel subscribers into Google Sheets
Bot listens for new subscribers and logs them to Google Sheets
"""

import logging
import gspread
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, ChatMemberHandler, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials
import os
from pathlib import Path

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


def get_gspread_client():
    """Get gspread client for Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"❌ Could not load Google Sheets credentials: {e}")
        return None


def log_subscriber(user_id: int, username: str = None):
    """Log subscriber to Google Sheets using gspread"""
    try:
        client = get_gspread_client()
        if not client:
            logger.error("❌ Google Sheets client not available")
            return False

        # Открываем таблицу
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        # Добавляем строку
        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])

        logger.info(f"✅ Logged subscriber: {user_id} (@{username}) - ADDED TO SHEET")
        return True

    except Exception as e:
        logger.error(f"❌ Error logging to Google Sheets: {e}")
        return False


def check_subscriber_in_sheet(user_id: int):
    """Проверяем, есть ли пользователь в таблице"""
    try:
        client = get_gspread_client()
        if not client:
            logger.error("❌ Google Sheets client not available")
            return False

        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1

        # Получаем все строки
        all_rows = worksheet.get_all_values()

        # Проверяем, есть ли пользователь
        for row in all_rows:
            if len(row) > 0 and row[0] == str(user_id):
                logger.info(f"✅ User {user_id} found in sheet!")
                return True

        logger.warning(f"❌ User {user_id} NOT found in sheet")
        return False

    except Exception as e:
        logger.error(f"❌ Error checking sheet: {e}")
        return False


async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track new channel members (subscribers)"""
    try:
        logger.info(f"🔔 track_chat_member called!")
        member_update = update.chat_member

        # Check if this is a subscription event
        if member_update.new_chat_member.status == 'member':
            if member_update.old_chat_member.status in ['left', 'restricted', None]:
                # New subscriber
                user_id = member_update.new_chat_member.user.id
                username = member_update.new_chat_member.user.username

                logger.info(f"✅ NEW SUBSCRIBER DETECTED: {user_id} (@{username})")

                # Log to Google Sheets
                logged = log_subscriber(user_id, username)

                if not logged:
                    logger.warning(f"❌ Failed to log subscriber {user_id}")
                    return

                logger.info(f"✅ User {user_id} successfully added to sheet!")

                # Отправляем сообщение подписчику в приватный чат
                try:
                    keyboard = [
                        [InlineKeyboardButton(
                            "🎁 Получить промокод на скидку",
                            url=f"https://t.me/senseandart/{PROMO_POST_ID}"
                        )]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 <b>Добро пожаловать!</b>\n\n"
                             "Спасибо что подписались на <b>@senseandart</b>!\n\n"
                             "👇 Нажмите кнопку ниже и получите <b>промокод на скидку</b>:",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    logger.info(f"✅ Auto-message sent to {user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not send auto-message to {user_id}: {e}")

    except Exception as e:
        logger.error(f"❌ Error in track_chat_member: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    username = update.effective_user.username

    logger.info(f"📝 /start command from {user_id} (@{username})")

    # Проверяем: подписан ли на канал?
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
    except:
        is_member = False

    if is_member:
        # Уже подписан - отправляем промокод
        keyboard = [
            [InlineKeyboardButton(
                "🎁 Получить промокод на скидку",
                url=f"https://t.me/senseandart/{PROMO_POST_ID}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
            "Вот ваш промокод на скидку:\n\n"
            "👇 Нажмите кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        # Не подписан - просим подписаться
        keyboard = [
            [InlineKeyboardButton(
                "📢 Подписаться на канал @senseandart",
                url="https://t.me/senseandart"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Подпишитесь на канал <b>@senseandart</b> и получите <b>промокод на скидку</b>!\n\n"
            "После подписки я автоматически пришлю вам промокод 🎁\n\n"
            "👇 Нажмите кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    logger.info(f"📝 Message from {user_id} (@{username}): {update.message.text}")

    # Проверяем: подписан ли на канал?
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
    except:
        is_member = False

    if is_member:
        # Уже подписан - отправляем промокод
        keyboard = [
            [InlineKeyboardButton(
                "🎁 Получить промокод на скидку",
                url=f"https://t.me/senseandart/{PROMO_POST_ID}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
            "Вот ваш промокод на скидку:\n\n"
            "👇 Нажмите кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        # Не подписан - просим подписаться
        keyboard = [
            [InlineKeyboardButton(
                "📢 Подписаться на канал @senseandart",
                url="https://t.me/senseandart"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Подпишитесь на канал <b>@senseandart</b> и получите <b>промокод на скидку</b>!\n\n"
            "После подписки я автоматически пришлю вам промокод 🎁\n\n"
            "👇 Нажмите кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"❌ Exception while handling an update: {context.error}")


def main():
    """Start the bot"""
    logger.info("🚀 Starting bot...")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add /start command handler
    application.add_handler(CommandHandler("start", start))

    # Add any message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))

    # Add handlers for channel member changes
    application.add_handler(ChatMemberHandler(track_chat_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(track_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("✅ Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
