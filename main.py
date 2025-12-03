#!/usr/bin/env python3
import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ЖЁСТКИЕ ЗНАЧЕНИЯ
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
PROMO_POST_ID = 42
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

added_users = set()


def get_gspread_client():
    """Подключение к Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return None


def log_subscriber(user_id: int, username: str = None):
    """Добавляем пользователя в Google Sheets"""
    
    # Если уже добавлен - пропускаем
    if user_id in added_users:
        return True

    try:
        logger.info(f"📝 Добавляю: {user_id} (@{username})")
        
        # Получаем клиент
        client = get_gspread_client()
        if not client:
            logger.error("❌ Клиент не подключен")
            return False

        # Открываем таблицу и лист
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1

        # Подготавливаем данные
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"
        row_data = [str(user_id), username_str, timestamp, 'subscribed']

        # Добавляем строку в таблицу
        worksheet.append_row(row_data)
        
        # Добавляем в кэш
        added_users.add(user_id)
        
        logger.info(f"✅ УСПЕХ! {user_id} добавлен в таблицу")
        return True

    except Exception as e:
        logger.error(f"❌ ОШИБКА при добавлении: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"

    logger.info(f"🎯 /START от {user_id} (@{username})")

    # Логируем в таблицу
    if log_subscriber(user_id, username):
        # Успешно добавлено - отправляем промокод
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

        await update.message.reply_text(thanks_text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"✅ Сообщение отправлено {user_id}")
    else:
        # Ошибка при добавлении
        error_text = "❌ Ошибка при записи в таблицу. Пожалуйста, попробуйте позже."
        await update.message.reply_text(error_text)
        logger.error(f"❌ Ошибка для {user_id}")


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    text = update.message.text

    logger.info(f"📨 Сообщение от {user_id}: {text}")

    # Логируем в таблицу
    if log_subscriber(user_id, username):
        # Успешно добавлено - отправляем промокод
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

        await update.message.reply_text(thanks_text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"✅ Сообщение отправлено {user_id}")
    else:
        # Ошибка при добавлении
        error_text = "❌ Ошибка при записи в таблицу. Пожалуйста, попробуйте позже."
        await update.message.reply_text(error_text)
        logger.error(f"❌ Ошибка для {user_id}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"❌ Ошибка: {context.error}")


def main():
    """Запуск бота"""
    logger.info("🚀 БОТ ЗАПУСКАЕТСЯ...")

    application = Application.builder().token(BOT_TOKEN).build()

    # Хэндлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    application.add_error_handler(error_handler)

    logger.info("✅ БОТ ГОТОВ!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
