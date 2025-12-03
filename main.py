#!/usr/bin/env python3
import gspread
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler, ChatMemberHandler
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CHANNEL_ID = -1001764760145
CHANNEL_USERNAME = 'senseandart'
PROMO_POST_ID = 42
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def add_to_sheet(user_id: int, username: str):
    """Добавляет пользователя в Google Sheets"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"
        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])
        logger.info(f"✅ Добавлен в таблицу: {user_id} ({username_str})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка таблицы: {e}")
        return False


async def send_promo(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str):
    """Отправляет промокод"""
    try:
        add_to_sheet(user_id, username)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
            ]),
            parse_mode='HTML'
        )
        logger.info(f"✅ Промокод отправлен: {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки промокода: {e}")


async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит подписку на канал"""
    my_chat_member = update.my_chat_member
    
    # Проверяем что это наш канал
    if my_chat_member.chat.id != CHANNEL_ID:
        return
    
    old_status = my_chat_member.old_chat_member.status
    new_status = my_chat_member.new_chat_member.status
    user_id = my_chat_member.from_user.id
    username = my_chat_member.from_user.username or "unknown"
    
    # Проверяем: был LEFT (не подписан) → стал MEMBER (подписан)
    if old_status == ChatMember.LEFT and new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        logger.info(f"🎉 Новый подписчик: {user_id} (@{username})")
        await send_promo(context, user_id, username)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start для тех кто уже подписан"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_subscribed = member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if is_subscribed:
            await send_promo(context, user_id, username)
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Пожалуйста, подпишитесь на @{CHANNEL_USERNAME}!</b>\n\n"
                     f"После подписки вы автоматически получите промокод.",
                parse_mode='HTML'
            )
            logger.info(f"📢 Запрос подписки: {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик подписки - АВТОМАТИЧЕСКИ отправляет промокод
    app.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Команда /start для ручной проверки
    app.add_handler(CommandHandler("start", start))
    
    logger.info("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
