import os
import logging


from utils.marzban_api import find_user_by_last4, generate_marzban_subscription
from utils.goods import get, get_callbacks
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
    serial4 = message.text.strip()
    if not serial4.isdigit() or len(serial4) != 4:
        return await message.reply("❌ Некорректный формат. Введите ровно 4 цифры.")
    # find user in panel by last4
    try:
        user = await find_user_by_last4(serial4)
    except Exception as e:
        return await message.reply("❌ Ошибка при обращении к панели, попробуйте позже.")
    if not user:
        return await message.reply("❌ Пользователь не найден. Проверьте цифры и повторите.")
    # save mapping in local DB
    from db.methods import create_vpn_profile
    await create_vpn_profile(message.from_user.id, user['username'])
    # save data in state for reference if needed
    await state.update_data(serial4=serial4, full_serial=user['username'])
    # show buy menu
    await message.answer(
        f"✅ Серийник подтверждён! Привет, {user.get('name', user['username'])}!\nВыберите подписку:",
        reply_markup=generate_products_keyboard()
    )
    await state.finish()
    # Сохраняем контекст
    await state.update_data(serial=serial, user=user)
    await message.answer(
        f"✅ Серийный номер подтверждён! Привет, {user.get('name', 'full_username')}! Выберите VPN-подписку для покупки:",
        reply_markup=generate_products_keyboard()
    )
    await state.finish()

def generate_products_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    goods = get()  # load list from goods.json
    for item in goods:
        title = item['title']
        cb = f"buy_{item['callback']}"
        kb.add(types.InlineKeyboardButton(f"{title}", callback_data=cb))
    return kb

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
