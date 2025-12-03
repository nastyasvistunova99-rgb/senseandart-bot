#!/usr/bin/env python3
import gspread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler
from oauth2client.service_account import ServiceAccountCredentials

BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CHANNEL_ID = -1001764760145
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
    except:
        pass


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
    except:
        pass


async def track_channel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит подписку на канал и сразу отправляет промокод"""
    my_chat_member = update.my_chat_member
    
    # Проверяем что это наш канал
    if my_chat_member.chat.id != CHANNEL_ID:
        return
    
    # Проверяем что произошла подписка (был LEFT, стал MEMBER)
    if my_chat_member.old_chat_member.status == ChatMember.LEFT and \
       my_chat_member.new_chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        
        user_id = my_chat_member.from_user.id
        username = my_chat_member.from_user.username or "unknown"
        
        # Добавляем в таблицу
        log_subscriber(user_id, username)
        
        # Отправляем промокод
        await send_promo(context, user_id)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ГЛАВНЫЙ ОБРАБОТЧИК - ловит подписку на канал
    application.add_handler(ChatMemberHandler(track_channel_subscription, ChatMemberHandler.MY_CHAT_MEMBER))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
