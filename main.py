#!/usr/bin/env python3
import sys
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# НАСТРОЙКИ
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
CHANNEL_ID = -1001764760145
CHANNEL_USERNAME = 'senseandart'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PROMO_POST_ID = 42


def add_to_sheet(user_id: int, username: str) -> bool:
    """Добавляет в Google Sheets"""
    try:
        logger.info(f"📝 Добавляю в таблицу: {user_id}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        display_username = f"@{username}" if username else f"ID_{user_id}"
        
        worksheet.append_row([str(user_id), display_username, timestamp, 'subscribed'])
        logger.info(f"✅ Таблица обновлена: {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка таблицы: {e}")
        return False


async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Проверяет подписку"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_subscribed = member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        logger.info(f"🔍 Проверка {user_id}: подписан={is_subscribed}")
        return is_subscribed
    except Exception as e:
        logger.error(f"❌ Ошибка проверки: {e}")
        return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "unknown"
        logger.info(f"📨 /start от {user_id} (@{username})")
        
        is_subscribed = await check_subscription(context, user_id)
        
        if is_subscribed:
            logger.info(f"✅ {user_id} подписан - отправляю промокод")
            add_to_sheet(user_id, username)
            
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")
                ]]),
                parse_mode='HTML'
            )
        else:
            logger.info(f"❌ {user_id} не подписан - отправляю запрос")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Пожалуйста, подпишитесь на канал @{CHANNEL_USERNAME}!</b>\n\nПосле подписки напишите /start и получите промокод.",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


def main():
    """Главная функция"""
    logger.info("🚀 ЗАПУСК БОТА")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    
    logger.info("✅ БОТ ГОТОВ!")
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    print("🔄 POLLING АКТИВЕН - СЛУШАЮ КОМАНДЫ...")
    
    # ТОЛЬКО polling - БЕЗ webhook!
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
