#!/usr/bin/env python3
import gspread
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
CHANNEL_ID = -1001764760145
CHANNEL_USERNAME = 'senseandart'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PROMO_POST_ID = 42


def add_subscriber_to_sheet(user_id: int, username: str) -> bool:
    """Добавляет подписчика в Google Sheets"""
    try:
        print(f"📝 Попытка добавить в таблицу: {user_id} (@{username})")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        display_username = f"@{username}" if username else f"User_{user_id}"
        
        worksheet.append_row([
            str(user_id),
            display_username,
            timestamp,
            'subscribed'
        ])
        
        logger.info(f"✅ УСПЕШНО ДОБАВЛЕН В ТАБЛИЦУ: {user_id} | {display_username}")
        print(f"✅ Таблица обновлена!")
        return True
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА ТАБЛИЦЫ: {str(e)}")
        print(f"❌ ОШИБКА: {str(e)}")
        return False


async def check_is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Проверяет подписан ли пользователь на канал"""
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        
        is_member = member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
        
        logger.info(f"🔍 Проверка подписки {user_id}: {is_member}")
        return is_member
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке подписки: {e}")
        return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    print("\n" + "="*50)
    print(f"📨 КОМАНДА /start ОТ ПОЛЬЗОВАТЕЛЯ: {user_id} (@{username})")
    print("="*50)
    
    logger.info(f"🎯 /start команда от пользователя {user_id}")
    
    # Проверяем подписку
    subscribed = await check_is_subscribed(context, user_id)
    
    if subscribed:
        print(f"✅ ПОЛЬЗОВАТЕЛЬ ПОДПИСАН!")
        logger.info(f"✅ Пользователь {user_id} подписан на канал")
        
        # Добавляем в таблицу
        add_subscriber_to_sheet(user_id, username)
        
        # Отправляем промокод
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n"
                    "👇 Нажмите кнопку и получите промокод на скидку:"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🎁 Получить промокод на скидку",
                        url=f"https://t.me/senseandart/{PROMO_POST_ID}"
                    )
                ]]),
                parse_mode='HTML'
            )
            logger.info(f"✅ Промокод отправлен пользователю {user_id}")
            print(f"✅ ПРОМОКОД ОТПРАВЛЕН!")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промокода: {e}")
            print(f"❌ Ошибка отправки: {e}")
    
    else:
        print(f"❌ ПОЛЬЗОВАТЕЛЬ НЕ ПОДПИСАН!")
        logger.info(f"❌ Пользователь {user_id} НЕ подписан на канал")
        
        # Просим подписаться
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"📢 <b>Пожалуйста, подпишитесь на канал @{CHANNEL_USERNAME}!</b>\n\n"
                    "Как только вы подпишетесь, напишите /start и получите промокод на скидку."
                ),
                parse_mode='HTML'
            )
            logger.info(f"📢 Запрос подписки отправлен пользователю {user_id}")
            print(f"📢 ЗАПРОС ПОДПИСКИ ОТПРАВЛЕН!")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки запроса: {e}")
            print(f"❌ Ошибка отправки: {e}")
    
    print("="*50 + "\n")


def main():
    """Главная функция"""
    print("\n🚀 ЗАПУСК БОТА...\n")
    logger.info("🚀 Запуск бота SenseandArt")
    
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик команды /start
    app.add_handler(CommandHandler("start", start_handler))
    
    logger.info("✅ Бот готов! Слушаю команды...")
    print("✅ БОТ ГОТОВ К РАБОТЕ!\n")
    
    # Запускаем polling
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
        print("Бот остановлен")


if __name__ == '__main__':
    main()
