#!/usr/bin/env python3
import os
import sys
import asyncio
import gspread
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, ContextTypes, CommandHandler
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🚀 ИНИЦИАЛИЗАЦИЯ БОТА")
print("=" * 60)

# НАСТРОЙКИ
BOT_TOKEN = '7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0'
CHANNEL_ID = -1001764760145
CHANNEL_USERNAME = 'senseandart'
GOOGLE_SHEETS_ID = '1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PROMO_POST_ID = 42

logger.info(f"BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"CHANNEL_USERNAME: {CHANNEL_USERNAME}")
logger.info(f"GOOGLE_SHEETS_ID: {GOOGLE_SHEETS_ID[:20]}...")


def add_to_sheet(user_id: int, username: str) -> bool:
    """Добавляет в таблицу"""
    try:
        logger.info(f"📝 Добавляю в таблицу: {user_id} (@{username})")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, 
            SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        worksheet = spreadsheet.sheet1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        display_username = f"@{username}" if username else f"ID_{user_id}"
        
        worksheet.append_row([
            str(user_id),
            display_username,
            timestamp,
            'subscribed'
        ])
        
        logger.info(f"✅ В таблицу добавлен: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка таблицы: {str(e)}")
        return False


async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Проверяет подписку"""
    try:
        logger.info(f"🔍 Проверяю подписку для {user_id}...")
        
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        
        is_subscribed = member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
        
        logger.info(f"📊 Результат проверки {user_id}: {is_subscribed}")
        return is_subscribed
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки подписки: {str(e)}")
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "unknown"
        
        print("\n" + "=" * 60)
        print(f"📨 /start ОТ: {user_id} (@{username})")
        print("=" * 60)
        logger.info(f"📨 /start от {user_id} (@{username})")
        
        # Проверяем подписку
        is_subscribed = await check_subscription(context, user_id)
        logger.info(f"Подписан: {is_subscribed}")
        
        if is_subscribed:
            print("✅ ПОЛЬЗОВАТЕЛЬ ПОДПИСАН")
            logger.info(f"✅ {user_id} подписан")
            
            # Добавляем в таблицу
            add_to_sheet(user_id, username)
            
            # Отправляем промокод
            msg_text = "🎉 <b>Спасибо что подписались на @senseandart!</b>\n\n👇 Нажмите кнопку и получите промокод на скидку:"
            
            await context.bot.send_message(
                chat_id=user_id,
                text=msg_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🎁 Получить промокод на скидку",
                        url=f"https://t.me/senseandart/{PROMO_POST_ID}"
                    )
                ]]),
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Промокод отправлен {user_id}")
            print("✅ ПРОМОКОД ОТПРАВЛЕН")
            
        else:
            print("❌ ПОЛЬЗОВАТЕЛЬ НЕ ПОДПИСАН")
            logger.info(f"❌ {user_id} не подписан")
            
            msg_text = f"📢 <b>Пожалуйста, подпишитесь на канал @{CHANNEL_USERNAME}!</b>\n\nПосле подписки напишите /start и получите промокод."
            
            await context.bot.send_message(
                chat_id=user_id,
                text=msg_text,
                parse_mode='HTML'
            )
            
            logger.info(f"📢 Запрос подписки отправлен {user_id}")
            print("📢 ЗАПРОС ПОДПИСКИ ОТПРАВЛЕН")
        
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В /start: {str(e)}")
        print(f"❌ ОШИБКА: {str(e)}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="❌ Произошла ошибка. Попробуйте позже."
            )
        except:
            logger.error("Не удалось отправить сообщение об ошибке")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"⚠️ ОШИБКА: {context.error}")
    print(f"⚠️ ОШИБКА: {context.error}")


def main():
    """Главная функция"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 ЗАПУСК БОТА")
        logger.info("=" * 60)
        print("\n🚀 СОЗДАЮ ПРИЛОЖЕНИЕ...\n")
        
        # Создаём приложение
        app = Application.builder().token(BOT_TOKEN).build()
        logger.info("✅ Приложение создано")
        print("✅ Приложение создано\n")
        
        # Добавляем обработчик /start
        app.add_handler(CommandHandler("start", start_command))
        logger.info("✅ Обработчик /start добавлен")
        print("✅ Обработчик /start добавлен\n")
        
        # Обработчик ошибок
        app.add_error_handler(error_handler)
        logger.info("✅ Обработчик ошибок добавлен")
        print("✅ Обработчик ошибок добавлен\n")
        
        logger.info("🟢 БОТ ГОТОВ! ЛОВЛЮ КОМАНДЫ...")
        print("🟢 БОТ ГОТОВ! СЛУШАЮ КОМАНДЫ...\n")
        print("=" * 60)
        print("ДЛЯ ОСТАНОВКИ НАЖМИ Ctrl+C")
        print("=" * 60 + "\n")
        
        # Запускаем polling
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА ПРИ ЗАПУСКЕ: {str(e)}")
        print(f"❌ ОШИБКА ПРИ ЗАПУСКЕ: {str(e)}")
        raise


if __name__ == '__main__':
    main()
