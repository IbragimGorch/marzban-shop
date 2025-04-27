import asyncio
import logging
import sys

import time
from datetime import datetime, timedelta

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
from app.database import bind_user, get_user
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
    user_data = get_user(message.from_user.id)
    if user_data:
        # Пользователь уже вводил серийник
        await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())
    else:
        # Новый пользователь
        await message.answer("Введите последние 4 цифры серийного номера роутера:")
        await state.set_state(SerialState.waiting_for_serial)

@router.callback_query(F.data == "My subscription 👤")
async def my_subscription(callback_query: types.CallbackQuery):
    user_data = get_user(callback_query.from_user.id)
    if user_data:
        sub_link = f"{glv.config['PANEL_HOST']}{user_data['subscription_url']}"
        await callback_query.message.answer(f"🔗 Ваша подписка: {sub_link}")
    else:
        await callback_query.message.answer("❌ Вы ещё не зарегистрированы. Нажмите /start.")
    await callback_query.answer()

@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = get_user(callback_query.from_user.id)
    if not user_data:
        await callback_query.message.answer("❌ Вы ещё не зарегистрированы. Нажмите /start и введите серийный номер.")
        await callback_query.answer()
        return

    # Спрашиваем Email снова для отправки нового чека
    await callback_query.message.answer("📧 Введите ваш email для новой оплаты:")
    await state.set_state(EmailState.waiting_for_email)
    await callback_query.answer()

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
    bind_user(
    tg_id=message.from_user.id,
    serial=serial4,
    username=user["username"],
    subscription_url=user["subscription_url"]
    )
    await message.answer("📧 Пожалуйста, введите ваш email для отправки чека:")
    await state.set_state(EmailState.waiting_for_email)

@router.message(EmailState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await message.answer("❌ Пожалуйста, введите корректный email!")
        return

    user_data = get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Пользователь не найден. Нажмите /start.")
        return

    # Сразу генерируем оплату
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

# Создадим простую память, чтобы не слать 100500 уведомлений
notified_users_24h = set()
notified_users_3h = set()

async def check_subscriptions():
    while True:
        users = glv.database.get_users()  # Функция из database.py
        now = time.time()

        for user_data in users:
            user = user_data['user']
            tg_id = user_data['tg_id']

            # Скачиваем пользователя по ID
            vpn_user = await find_user_by_last4(user_data['serial'])

            if not vpn_user:
                continue

            expire = vpn_user.get('expire')
            if not expire:
                continue

            time_left = expire - now

            # Если меньше 1 суток и пользователь ещё не уведомлен
            if 0 < time_left < 86400 and tg_id not in notified_users_24h:
                try:
                    await bot.send_message(
                        tg_id,
                        "⏰ Ваша подписка истекает через 24 часа! Не забудьте продлить, чтобы избежать отключения.",
                        reply_markup=get_main_keyboard()
                    )
                    notified_users_24h.add(tg_id)
                except Exception as e:
                    logging.error(f"Не смог отправить уведомление за 24 часа: {e}")

            # Если меньше 3 часов и пользователь ещё не уведомлен
            if 0 < time_left < 10800 and tg_id not in notified_users_3h:
                try:
                    await bot.send_message(
                        tg_id,
                        "⚡ Внимание! Подписка истекает через 3 часа! Последний шанс продлить без перебоев!",
                        reply_markup=get_main_keyboard()
                    )
                    notified_users_3h.add(tg_id)
                except Exception as e:
                    logging.error(f"Не смог отправить уведомление за 3 часа: {e}")

        await asyncio.sleep(1800)  # Проверяем каждые 30 минут

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


    # 🚀 Запускаем фоновую проверку подписок
    asyncio.create_task(check_subscriptions())

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
