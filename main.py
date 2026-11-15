import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==========================================================
# КОНФИГУРАЦИЯ
# ==========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
WELCOME_FILE = "welcome.txt"

# Текст по умолчанию (если файла еще нет)
DEFAULT_WELCOME = (
    "привет, ты попал в анон мэди🤍\n"
    "- напиши, что хочешь, чтобы передалось анонимно!\n"
    "все абсолютно анонимно, можете не переживать🐾"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================================
# РАБОТА С ФАЙЛОМ ПРИВЕТСТВИЯ
# ==========================================================
def get_welcome_text() -> str:
    """Читает текст из файла. Если файла нет — возвращает текст по умолчанию."""
    if os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return DEFAULT_WELCOME


def save_welcome_text(text: str):
    """Сохраняет новый текст в файл."""
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        f.write(text)


# ==========================================================
# МАШИНА СОСТОЯНИЙ (FSM) ДЛЯ СМЕНЫ ТЕКСТА
# ==========================================================
class AdminStates(StatesGroup):
    waiting_for_new_welcome = State()


# ==========================================================
# ОБРАБОТЧИКИ КОМАНД
# ==========================================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Берем актуальный текст из файла
    welcome_text = get_welcome_text()
    await message.answer(welcome_text)


@dp.message(Command("set_welcome"))
async def cmd_set_welcome(message: Message, state: FSMContext):
    # Проверяем, что команду ввел именно админ
    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(AdminStates.waiting_for_new_welcome)
    await message.answer(
        "✍️ Отправь мне новый текст приветствия одним сообщением.\n"
        "Он сразу же применится для всех пользователей.\n\n"
        "Чтобы отменить, напиши /cancel"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("❌ Изменение текста отменено.")


@dp.message(AdminStates.waiting_for_new_welcome)
async def process_new_welcome(message: Message, state: FSMContext):
    # Сохраняем новый текст в файл
    save_welcome_text(message.text)
    await state.clear()
    await message.answer("✅ Текст приветствия успешно обновлен!")


# ==========================================================
# ОБРАБОТЧИК ПЕРЕСЫЛКИ СООБЩЕНИЙ
# ==========================================================
@dp.message(F.chat.type == "private")
async def forward_to_admin(message: Message):
    user = message.from_user

    # Игнорируем команды и сообщения от админа
    if message.text and message.text.startswith("/"):
        return
    if user.id == ADMIN_ID:
        return

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

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=sender_info,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.exception("Не удалось переслать сообщение админу: %s", e)


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
