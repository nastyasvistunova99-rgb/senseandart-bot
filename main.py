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

added_users = set()


def log_subscriber(user_id: int, username: str):
    if user_id in added_users:
        return
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username_str = f"@{username}" if username else f"User_{user_id}"
        worksheet.append_row([str(user_id), username_str, timestamp, 'subscribed'])
        added_users.add(user_id)
        logger.info(f"✅ Added to sheet: {user_id} (@{username})")
    except Exception as e:
        logger.error(f"❌ Error adding to sheet: {e}")


async def send_promo(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Получить промокод на скидку", url=f"https://t.me/senseandart/{PROMO_POST_ID}")]
            ]),
            parse_mode='HTML'
        )
        logger.info(f"✅ Promo sent to {user_id}")
    except Exception as e:
        logger.error(f"❌ Error sending promo to {user_id}: {e}")


async def send_subscribe_message(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📢 <b>Пожалуйста, подпишитесь на канал @{CHANNEL_USERNAME}!</b>\n\n"
                 f"После подписки нажмите /start и получите промокод на скидку.",
            parse_mode='HTML'
        )
        logger.info(f"📢 Subscribe message sent to {user_id}")
    except Exception as e:
        logger.error(f"❌ Error sending subscribe message to {user_id}: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет подписку и отправляет промокод"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    try:
        # Проверяем статус пользователя в канале
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            # Пользователь подписан!
            logger.info(f"✅ User {user_id} is subscribed")
            log_subscriber(user_id, username)
            await send_promo(context, user_id)
        else:
            # Пользователь НЕ подписан
            logger.info(f"❌ User {user_id} is NOT subscribed")
            await send_subscribe_message(context, user_id)
            
    except Exception as e:
        logger.error(f"❌ Error checking subscription: {e}")
        await send_subscribe_message(context, user_id)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команда /start - проверяет подписку
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик подписки (на случай если бот админ канала)
    application.add_handler(ChatMemberHandler(lambda u, c: None, ChatMemberHandler.MY_CHAT_MEMBER))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == '__main__':
    main()
