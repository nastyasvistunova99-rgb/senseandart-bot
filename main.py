#!/usr/bin/env python3
import logging
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler
from telegram.error import TelegramError
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CHANNEL_ID = -1001764760145
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


async def send_promo(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет промокод пользователю"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
            ]),
            parse_mode='HTML'
        )
    except:
        pass


async def track_channel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит подписку/отписку от канала"""
    my_chat_member = update.my_chat_member
    
    # Проверяем что это подписка в канале
    if my_chat_member.chat.id != CHANNEL_ID:
        return
    
    # Проверяем статус: был ли пользователь раньше не членом, теперь стал членом?
    if my_chat_member.old_chat_member.status == ChatMember.LEFT and \
       my_chat_member.new_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        
        user_id = my_chat_member.from_user.id
        username = my_chat_member.from_user.username or "unknown"
        
        logger.info(f"👤 {user_id} подписался на канал!")
        
        # Добавляем в таблицу
        log_subscriber(user_id, username)
        
        # Отправляем промокод
        await send_promo(context, user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Добавляем в таблицу
    log_subscriber(user_id, username)
    
    # Отправляем промокод
    await send_promo(context, user_id)


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Добавляем в таблицу
    log_subscriber(user_id, username)
    
    # Отправляем промокод
    await send_promo(context, user_id)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик подписки на канал
    application.add_handler(ChatMemberHandler(track_channel_subscription, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    
    logger.info("✅ БОТ ЗАПУЩЕН")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
