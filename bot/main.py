import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
BOT_TOKEN       = os.getenv("BOT_TOKEN")
PANEL_HOST      = os.getenv("PANEL_HOST")
PANEL_API_TOKEN = os.getenv("PANEL_API_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp  = Dispatcher(bot, storage=MemoryStorage())

# --- FSM States ---
class SerialState(StatesGroup):
    waiting_for_serial = State()

# --- /start handler ---
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "👋 Привет! Введите последние 4 цифры серийного номера вашего роутера, чтобы продолжить настройку и покупку VPN-подписки:"
    )
    await SerialState.waiting_for_serial.set()

# --- Serial input and user verification ---
@dp.message_handler(state=SerialState.waiting_for_serial)
async def process_serial(message: types.Message, state: FSMContext):
    serial = message.text.strip()
    if not serial.isdigit() or len(serial) != 4:
        return await message.reply("❌ Некорректный формат. Введите ровно 4 цифры серийного номера.")
    full_username = serial  # Assuming username equals full serial number
    headers = {
        "Authorization": f"Bearer {PANEL_API_TOKEN}",
        "Content-Type": "application/json"
    }
    # Проверяем наличие пользователя в панели Marzban
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_HOST}/api/users/{full_username}", headers=headers) as resp:
            if resp.status != 200:
                await message.answer(
                    "❌ Пользователь с таким серийным номером не найден. Проверьте ввод и попробуйте снова."
                )
                await state.finish()
                return
            user = await resp.json()
    # Сохраняем контекст
    await state.update_data(serial=serial, user=user)
    await message.answer(
        f"✅ Серийный номер подтверждён! Привет, {user.get('name', full_username')}! Выберите VPN-подписку для покупки:",
        reply_markup=generate_products_keyboard()
    )
    await state.finish()

# --- Generate inline keyboard for products ---
def generate_products_keyboard():
    # Здесь нужно получить список товаров из панельного API или локального файла
    # Пример статического списка:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("1 месяц - $5", callback_data="buy_1m"))
    keyboard.add(types.InlineKeyboardButton("3 месяца - $12", callback_data="buy_3m"))
    keyboard.add(types.InlineKeyboardButton("12 месяцев - $40", callback_data="buy_12m"))
    return keyboard

# --- Callback для покупки ---
@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_purchase(callback_query: types.CallbackQuery):
    period = callback_query.data.split('_')[1]
    # Запуск процесса оплаты (реализуйте логику платежа через ваш API)
    pay_link = await create_payment_link(period, callback_query.from_user.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"Перейдите по ссылке для оплаты выбранного периода ({period}):\n{pay_link}"
    )
    await bot.answer_callback_query(callback_query.id)

# --- Создание ссылки на оплату ---
async def create_payment_link(period: str, telegram_user_id: int) -> str:
    # Заглушка: замените на вызов вашего платежного API (YooKassa, Cryptomus и т.д.)
    return f"{PANEL_HOST}/pay?user={telegram_user_id}&period={period}"

# --- Entry point ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
