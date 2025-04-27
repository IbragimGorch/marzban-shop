import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router, types, enums
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from utils.marzban_api import find_user_by_last4
from utils.yookassa import create_payment as yk_create_payment
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.pay import get_pay_keyboard
from app.routes import check_yookassa_payment
import glv

# States
from aiogram.fsm.state import State, StatesGroup

class SerialState(StatesGroup):
    waiting_for_serial = State()

class EmailState(StatesGroup):
    waiting_for_email = State()

# Инициализация логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Инициализация бота
bot = Bot(token=glv.config['BOT_TOKEN'], parse_mode=enums.ParseMode.HTML)
glv.bot = bot
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = web.Application()
i18n = I18n(path=Path(__file__).parent / "locales", default_locale="en", domain="bot")
i18n_middleware = SimpleI18nMiddleware(i18n=i18n)
dp.update.middleware(i18n_middleware)

router = Router()

dp.include_router(router)

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Введите последние 4 цифры серийного номера роутера:")
    await state.set_state(SerialState.waiting_for_serial)

@router.message(SerialState.waiting_for_serial)
async def process_serial(message: types.Message, state: FSMContext):
    serial4 = message.text.strip()
    if not serial4.isdigit() or len(serial4) != 4:
        await message.answer("❌ Введите корректные 4 цифры серийного номера!")
        return

    user = await find_user_by_last4(serial4)
    if not user:
        await message.answer("❌ Пользователь не найден. Проверьте цифры и попробуйте снова.")
        return

    await state.update_data(serial=serial4, user=user)
    await message.answer("📧 Пожалуйста, введите ваш email для отправки чека:")
    await state.set_state(EmailState.waiting_for_email)

@router.message(EmailState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await message.answer("❌ Пожалуйста, введите корректный email!")
        return

    data = await state.get_data()
    serial = data.get("serial")
    user = data.get("user")

    # Создание платежа
    payment = await yk_create_payment(
        tg_id=message.from_user.id,
        callback="m1",
        email=email,
        chat_id=message.chat.id,
        lang_code=message.from_user.language_code
    )

    await message.answer(
        f"💳 Сумма к оплате: {payment['amount']}₽\nНажмите кнопку ниже для оплаты:",
        reply_markup=get_pay_keyboard(payment["url"])
    )
    await state.clear()

async def on_startup(bot: Bot):
    webhook_url = f"{glv.config['WEBHOOK_URL']}/webhook"
    await bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook set to {webhook_url}")

async def main():
    await on_startup(bot)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    app.router.add_post("/yookassa_payment", check_yookassa_payment)

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", glv.config['WEBHOOK_PORT'])
    await site.start()

    logging.info("Bot started and webhook is ready!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
