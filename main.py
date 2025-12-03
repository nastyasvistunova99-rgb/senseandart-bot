#!/usr/bin/env python3
"""
Telegram Bot - записывает пользователей в Google Sheets и отправляет промокод
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

logger.info("=" * 70)
logger.info("🚀 БОТ ЗАПУСКАЕТСЯ")
logger.info(f"📌 GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID}")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 PROMO_POST_ID: {PROMO_POST_ID}")
logger.info("=" * 70)

added_users = set()


def get_gspread_client():
    """Подключение к Google Sheets"""
    try:
        logger.info(f"🔑 Загружаю credentials...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, SCOPES)
        
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets подключен!")
        return client
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА подключения: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def log_subscriber(user_id: int, username: str = None):
    """Добавляем пользователя в Google Sheets"""
    try:
        if user_id in added_users:
            logger.info(f"⏭️ User {user_id} уже в кэше")
            return True

        logger.info(f"\n{'='*70}")
        logger.info(f"📝 ЗАПИСЫВАЮ В ТАБЛИЦУ: {user_id} (@{username})")
        logger.info(f"{'='*70}")

        client = get_gspread_client()
        if not client:
            logger.error("❌ Нет подключения к Google Sheets!")
            return False

        logger.info(f"📂 Открываю таблицу {GOOGLE_SHEETS_ID}...")
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        logger.info(f"✅ Таблица: {spreadsheet.title}")
        
        worksheet = spreadsheet.sheet1
        logger.info(f"✅ Лист: {worksheet.title}")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"

        row_data = [str(user_id), username_str, timestamp, 'subscribed']
        logger.info(f"📥 Добавляю: {row_data}")
        
        worksheet.append_row(row_data)

        added_users.add(user_id)

        logger.info(f"🎉🎉🎉 УСПЕХ! Добавлен в таблицу!")
        logger.info(f"{'='*70}\n")
        return True

    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    first_name = update.effective_user.first_name or "Friend"

    logger.info(f"\n🎯 /START от {user_id} (@{username})")

    # СРАЗУ логируем в таблицу (без проверки подписки!)
    logged = log_subscriber(user_id, username)

    if logged:
        # Отправляем сообщение благодарности
        thanks_text = (
            "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
            "👇 Нажмите кнопку и получите промокод на скидку:"
        )
        
        keyboard = [
            [InlineKeyboardButton(
                "🎁 Получить промокод на скидку",
                url=f"https://t.me/senseandart/{PROMO_POST_ID}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            thanks_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"✅ Сообщение отправлено {user_id}")
    else:
        error_text = (
            "❌ Ошибка при записи в таблицу.\n"
            "Пожалуйста, попробуйте позже."
        )
        await update.message.reply_text(error_text)
        logger.error(f"❌ Ошибка записи для {user_id}")


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    text = update.message.text

    logger.info(f"\n📨 СООБЩЕНИЕ от {user_id}: {text}")

    # СРАЗУ логируем в таблицу (без проверки подписки!)
    logged = log_subscriber(user_id, username)

    if logged:
        # Отправляем сообщение благодарности
        thanks_text = (
            "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
            "👇 Нажмите кнопку и получите промокод на скидку:"
        )
        
        keyboard = [
            [InlineKeyboardButton(
                "🎁 Получить промокод на скидку",
                url=f"https://t.me/senseandart/{PROMO_POST_ID}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            thanks_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"✅ Сообщение отправлено {user_id}")
    else:
        error_text = (
            "❌ Ошибка при записи в таблицу.\n"
            "Пожалуйста, попробуйте позже."
        )
        await update.message.reply_text(error_text)
        logger.error(f"❌ Ошибка записи для {user_id}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"❌ ОШИБКА: {context.error}")
    import traceback
    logger.error(traceback.format_exc())


def main():
    """Запуск бота"""
    logger.info("\n" + "=" * 70)
    logger.info("🚀🚀🚀 ЗАПУСКАЮ БОТ...")
    logger.info("=" * 70 + "\n")

    application = Application.builder().token(BOT_TOKEN).build()

    # Хэндлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    application.add_error_handler(error_handler)

    # Запуск
    logger.info("✅✅✅ БОТ ГОТОВ!")
    logger.info("=" * 70 + "\n")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
