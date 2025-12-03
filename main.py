#!/usr/bin/env python3
import asyncio
import gspread
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# КОНСТАНТЫ
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CHANNEL_ID = -1001764760145
CHANNEL_USERNAME = 'senseandart'
PROMO_POST_ID = 42
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def save_to_sheet(user_id: int, username: str) -> bool:
    """Добавляет пользователя в Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_display = f"@{username}" if username else f"ID_{user_id}"
        
        worksheet.append_row([str(user_id), username_display, timestamp, 'subscribed'])
        logger.info(f"✅ Таблица: {user_id} | {username_display}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка таблицы: {e}")
        return False


async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Проверяет подписку пользователя"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.error(f"❌ Ошибка проверки подписки: {e}")
        return False


async def send_promo_message(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Отправляет сообщение с благодарностью и промокодом"""
    try:
        text = (
            "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
            "👇 Нажмите кнопку и получите промокод на скидку:"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Получить промокод", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
        ])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info(f"✅ Промокод отправлен: {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки промокода: {e}")


async def send_subscribe_request(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Просит подписаться на канал"""
    try:
        text = (
            f"📢 <b>Пожалуйста, подпишитесь на @{CHANNEL_USERNAME}!</b>\n\n"
            "После подписки бот автоматически отправит вам промокод на скидку."
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML'
        )
        logger.info(f"📢 Запрос подписки отправлен: {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки запроса: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главная команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    logger.info(f"📨 /start от {user_id} (@{username})")
    
    # Проверяем подписку
    is_subscribed = await check_subscription(context, user_id)
    
    if is_subscribed:
        # Пользователь подписан - отправляем промокод
        logger.info(f"✅ Пользователь уже подписан: {user_id}")
        save_to_sheet(user_id, username)
        await send_promo_message(context, user_id)
    else:
        # Пользователь НЕ подписан - просим подписаться
        logger.info(f"❌ Пользователь не подписан: {user_id}")
        await send_subscribe_request(context, user_id)


def main() -> None:
    """Запуск бота"""
    logger.info("🤖 Запуск бота...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем команду /start
    app.add_handler(CommandHandler("start", start_command))
    
    logger.info("🟢 Бот готов!")
    
    # Запускаем polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
