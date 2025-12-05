#!/usr/bin/env python3
"""
🤖 Простой Telegram Bot с POLLING
✅ Собирает подписчиков в локальную базу SQLite (subscribers.db)
✅ Отправляет промокод в приватный чат
✅ По /export шлёт CSV со списком подписчиков
"""

import logging
import sqlite3
from io import StringIO
from pathlib import Path
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, ChatMemberHandler, CommandHandler

# ================== ЛОГИРОВАНИЕ ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================== ПАРАМЕТРЫ ==================
BOT_TOKEN = "7904726862:AAFG3CurCeRels3tXl_agIYYzhn6vBNlk0c"
CHANNEL_ID = -1001764760145
PROMO_POST_ID = 42

DB_PATH = Path("subscribers.db")

logger.info("=" * 50)
logger.info(f"📌 BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"📌 CHANNEL_ID: {CHANNEL_ID}")
logger.info(f"📌 DB_PATH: {DB_PATH}")
logger.info("=" * 50)

# ================== БАЗА ДАННЫХ ==================
def init_db() -> None:
    """Создать БД и таблицу, если их нет."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                joined_at TEXT,
                status TEXT
            )
            """
        )
        conn.commit()
        conn.close()
        logger.info("✅ База subscribers.db готова")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")


def log_subscriber(user_id: int, username: str | None = None) -> bool:
    """Добавить подписчика в локальную БД SQLite."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username_str = f"@{username}" if username else f"User_{user_id}"

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO subscribers (user_id, username, joined_at, status) "
            "VALUES (?, ?, ?, ?)",
            (user_id, username_str, timestamp, "subscribed"),
        )
        conn.commit()
        conn.close()

        logger.info(f"✅ Добавлен в БД: {user_id} ({username_str})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка добавления в БД: {e}")
        return False


def export_subscribers_csv() -> str:
    """Вернуть подписчиков в виде CSV-строки."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, joined_at, status FROM subscribers")
    rows = cur.fetchall()
    conn.close()

    buf = StringIO()
    buf.write("user_id,username,joined_at,status\n")
    for r in rows:
        buf.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")
    buf.seek(0)
    return buf.getvalue()

# ================== ОБРАБОТЧИКИ ==================
async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживание новых подписчиков."""
    try:
        member_update = update.chat_member
        new_status = member_update.new_chat_member.status
        old_status = (
            member_update.old_chat_member.status
            if member_update.old_chat_member
            else None
        )

        # интересует только реальный переход "был не в канале" -> "стал member"
        if new_status == "member" and old_status in ["left", "kicked", "restricted", None]:
            user_id = member_update.new_chat_member.user.id
            username = member_update.new_chat_member.user.username
            first_name = member_update.new_chat_member.user.first_name

            logger.info(
                f"✅ НОВЫЙ ПОДПИСЧИК: {user_id} (@{username}) - {first_name}"
            )

            # Логируем в локальную БД
            log_subscriber(user_id, username)

            # Отправляем приватное сообщение
            try:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🎁 Получить промокод на скидку",
                            url=f"https://t.me/senseandart/{PROMO_POST_ID}",
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🎉 <b>Добро пожаловать!</b>\n\n"
                        "Спасибо, что подписались на <b>@senseandart</b>!\n\n"
                        "👇 Нажмите кнопку и получите <b>промокод на скидку</b>:"
                    ),
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
                logger.info(f"✅ Сообщение отправлено {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка отправки: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка обработчика: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start."""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        logger.info(f"📝 /start от {user_id} (@{username})")

        # Проверяем подписку через get_chat_member
        try:
            member = await context.bot.get_chat_member(
                chat_id=CHANNEL_ID, user_id=user_id
            )
            status = member.status
            logger.info(f"get_chat_member для {user_id}: {member!r}")
            is_member = status in ["member", "administrator", "creator"]
            logger.info(f"Статус пользователя в канале: {status}")
        except Exception as e:
            logger.warning(f"Не удалось получить статус подписки: {e}")
            is_member = False

        if is_member:
            # Уже подписан -> сразу даём промокод
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🎁 Получить промокод на скидку",
                        url=f"https://t.me/senseandart/{PROMO_POST_ID}",
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🎉 <b>Спасибо, что вы уже подписаны на @senseandart!</b>\n\n"
                "👇 Заберите ваш промокод по кнопке ниже:",
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        else:
            # Не подписан — просим подписаться
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📢 Подписаться на канал @senseandart",
                        url="https://t.me/senseandart",
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Подпишитесь на канал <b>@senseandart</b> и получите "
                "<b>промокод на скидку</b>!\n\n"
                "После подписки я автоматически пришлю вам промокод 🎁\n\n"
                "👇 Нажмите кнопку ниже:",
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"❌ Ошибка /start: {e}")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить CSV с подписчиками."""
    try:
        csv_text = export_subscribers_csv()
        if not csv_text.strip() or csv_text.strip() == "user_id,username,joined_at,status":
            await update.message.reply_text("Пока нет ни одного подписчика.")
            return

        await update.message.reply_document(
            document=csv_text.encode("utf-8"),
            filename="subscribers.csv",
            caption="Подписчики в CSV",
        )
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта: {e}")
        await update.message.reply_text("Не удалось выгрузить подписчиков.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок."""
    logger.error(f"❌ Ошибка: {context.error}")

# ================== ГЛАВНАЯ ФУНКЦИЯ ==================
def main():
    """Запуск бота."""
    logger.info("🚀 Инициализация приложения...")
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    logger.info("📝 Добавляем обработчики...")
    application.add_handler(
        ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER)
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_error_handler(error_handler)

    logger.info("✅ Обработчики добавлены")
    logger.info("🔄 Запускаем POLLING...")

    application.run_polling(timeout=30, allowed_updates=["chat_member", "message"])


if __name__ == "__main__":
    main()
