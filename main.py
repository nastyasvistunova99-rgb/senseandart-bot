#!/usr/bin/env python3
import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CHANNEL_ID = -1001764760145  # ID канала @senseandart
PROMO_POST_ID = 42
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

added_users = set()


def get_gspread_client():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        return gspread.authorize(creds)
    except:
        return None


def log_subscriber(user_id: int, username: str):
    if user_id in added_users:
        return
    
    try:
        client = get_gspread_client()
        if client:
            spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
            worksheet = spreadsheet.sheet1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            username_str = f"@{username}" if username else f"User_{user_id}"
            worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])
            added_users.add(user_id)
            logger.info(f"✅ Добавлен: {user_id}")
    except:
        logger.error(f"❌ Ошибка для {user_id}")


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет подписан ли пользователь на канал"""
    try:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        
        # Если статус НЕ в списке допустимых - не подписан
        if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            return False
        return True
    except TelegramError:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Проверяем подписку
    if not await check_subscription(update, context):
        await update.message.reply_text(
            "❌ <b>Вы не подписаны на канал @senseandart!</b>\n\n"
            "👇 Нажмите кнопку, подпишитесь и напишите боту /start заново:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться на @senseandart", url="https://t.me/senseandart")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Добавляем в таблицу
    log_subscriber(user_id, username)
    
    # Отправляем промокод
    await update.message.reply_text(
        "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
        ]),
        parse_mode='HTML'
    )


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Проверяем подписку
    if not await check_subscription(update, context):
        await update.message.reply_text(
            "❌ <b>Вы не подписаны на канал @senseandart!</b>\n\n"
            "👇 Нажмите кнопку, подпишитесь и напишите боту заново:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться на @senseandart", url="https://t.me/senseandart")]
            ]),
            parse_mode='HTML'
        )
        return
    
    # Добавляем в таблицу
    log_subscriber(user_id, username)
    
    # Отправляем промокод
    await update.message.reply_text(
        "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
        ]),
        parse_mode='HTML'
    )


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    logger.info("✅ БОТ ЗАПУЩЕН")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
