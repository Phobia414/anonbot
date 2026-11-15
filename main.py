import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# ==========================================================
# КОНФИГУРАЦИЯ
# ==========================================================
# Токен бота: рекомендуется брать из переменной окружения,
# но можно захардкодить для локального теста.
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
# ==========================================================
# ЛОГИРОВАНИЕ
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================================================
# БОТ И ДИСПЕТЧЕР
# ==========================================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================================
# ОБРАБОТЧИК ВСЕХ ЛИЧНЫХ СООБЩЕНИЙ
# ==========================================================
@dp.message(F.chat.type == "private")
async def forward_to_admin(message: Message):
    """
    Пересылает любое личное сообщение единственному администратору.
    Сначала — данные отправителя, затем — копию самого сообщения.
    """
    user = message.from_user

    # --- Фильтры ---
    # 1. Игнорируем команды (начинаются с "/") в текстовых сообщениях
    if message.text and message.text.startswith("/"):
        return

    # 2. Игнорируем сообщения от самого администратора,
    #    чтобы не было зацикливания
    if user.id == ADMIN_ID:
        return

    # --- Формируем блок с данными отправителя ---
    sender_info_parts = [
        "👤 <b>Отправитель</b>",
        f'• Имя: <a href="tg://user?id={user.id}">{user.full_name}</a>',
    ]
    if user.username:
        sender_info_parts.append(f"• Юзернейм: @{user.username}")
    else:
        sender_info_parts.append("• Юзернейм: <i>не установлен</i>")
    sender_info_parts.append(f"• ID: <code>{user.id}</code>")

    sender_info = "\n".join(sender_info_parts)

    # --- Отправка ---
    try:
        # 1. Данные отправителя ПЕРВЫМ сообщением
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=sender_info,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        # 2. Копия самого сообщения ВТОРЫМ (без "Переслано от...")
        await bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.exception("Не удалось переслать сообщение админу: %s", e)

    # Пользователю НИЧЕГО не отвечаем — он не должен знать о пересылке


# ==========================================================
# ЗАПУСК
# ==========================================================
async def main():
    logger.info("Бот запускается. Получатель: %s", ADMIN_ID)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")