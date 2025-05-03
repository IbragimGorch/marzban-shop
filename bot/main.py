from aiogram.fsm.state import State, StatesGroup

class SerialState(StatesGroup):
    waiting_for_serial = State()

class EmailState(StatesGroup):
    waiting_for_email = State()

import asyncio
import logging
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, F, Router, types, enums
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from db.methods import (
    add_yookassa_payment,
    get_yookassa_payment,
    delete_payment,
    get_vpn_user_by_username
)

from utils.marzban_api import find_user_by_last4, find_user_by_username
from utils.yookassa import create_payment as yk_create_payment
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.pay import get_pay_keyboard
from app.routes import check_yookassa_payment
from app.database import save_user, get_user, get_all_users, mark_user_notified


import glv

# Инициализация логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")



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

active_panels = {}


from handlers.commands import register_commands
from handlers.messages import register_messages
from handlers.callbacks import register_callbacks

register_commands(dp)
register_messages(dp)
register_callbacks(dp)


print(">>> Бот стартанул!!! <<<", flush=True)
logging.info(">>> Логгер бот стартанул <<<")



async def send_or_edit(message: types.Message, text: str, state: FSMContext, keyboard=None):
    data = await state.get_data()
    old_msg_id = data.get("last_msg_id")

    try:
        if old_msg_id:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=old_msg_id,
                text=text,
                reply_markup=keyboard
            )
        else:
            sent = await message.answer(text, reply_markup=keyboard)
            await state.update_data(last_msg_id=sent.message_id)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось отредактировать сообщение, отправляем новое: {e}")
        sent = await message.answer(text, reply_markup=keyboard)
        await state.update_data(last_msg_id=sent.message_id)

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_data = get_user(message.from_user.id)
    if user_data:
        await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("Введите последние 4 цифры серийного номера роутера:")
        await state.set_state(SerialState.waiting_for_serial)



@router.message(Command("panel"))
async def send_panel(message: types.Message, state: FSMContext):
    user_data = get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы ещё не зарегистрированы. Нажмите /start.")
        return

    vpn_user = await find_user_by_last4(user_data['username'])
    if not vpn_user:
        await message.answer("❌ Пользователь не найден в панели.")
        return

    text = build_panel_text(vpn_user)
    sent_message = await message.answer(text)

    # Запоминаем сообщение для обновления
    active_panels[message.from_user.id] = {
        "chat_id": sent_message.chat.id,
        "message_id": sent_message.message_id,
        "vpn_username": user_data['username']
    }

async def update_panels():
    while True:
        for user_id, data in active_panels.items():
            try:
                vpn_user = await find_user_by_username(data['vpn_username'])
                if vpn_user:
                    new_text = build_panel_text(vpn_user)
                    await bot.edit_message_text(
                        chat_id=data["chat_id"],
                        message_id=data["message_id"],
                        text=new_text
                    )
            except Exception as e:
                logging.error(f"Ошибка при обновлении панели у {user_id}: {e}")
        await asyncio.sleep(60)  # Обновлять раз в минуту

def build_panel_text(vpn_user: dict) -> str:
    expire_ts = vpn_user.get("expire")
    expire_text = datetime.fromtimestamp(expire_ts).strftime("%d.%m.%Y %H:%M") if expire_ts else "неизвестно"
    used = (vpn_user.get("used_traffic") or 0) // (1024**3)
    limit = (vpn_user.get("data_limit") or 0) // (1024**3)
    status = vpn_user.get("status", "неизвестно").upper()

    return (
        f"📶 Подписка активна до: <b>{expire_text}</b>\n"
        f"⚡ Статус: <b>{status}</b>\n"
    )

@router.message(F.text == __("📊 My subscription"))
async def handle_my_panel_button(message: types.Message, state: FSMContext):
    await send_panel(message, state)
#
#
#
#@router.message(F.text == "Support ❤️")
#async def support_handler(message: types.Message):
#    await send_or_edit(message, "💬 Поддержка: {glv.config['SUPPORT_LINK']}", state, get_back_keyboard())
#
#@router.message(F.text == "Frequent questions ℹ️")
#async def faq_handler(message: types.Message):
#    await send_or_edit(message, "📖 Частые вопросы: {glv.config['RULES_LINK']}", state, get_back_keyboard())
#
#@router.message(F.text == "Join 🏄🏻‍♂️")
#async def join_handler(message: types.Message):
#    await message.answer("💥 Чтобы подключиться, выберите 'Оплатить подписку' через /start или кнопку на экране!")
#


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
    user = data.get("user")

    save_user(
        telegram_id=message.from_user.id,
        username=user['username'],
        subscription_url=user['subscription_url'],
        email=email
    )

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

@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("📧 Введите ваш email для оплаты подписки:")
    await state.set_state(EmailState.waiting_for_email)
    await callback_query.answer()


@router.callback_query(F.data == "my_subscription")
async def my_subscription(callback_query: types.CallbackQuery):
    user_data = get_user(callback_query.from_user.id)
    if not user_data:
        await callback_query.message.answer("❌ Пользователь не найден. Нажмите /start.")
        await callback_query.answer()
        return

    subscription_url = f"{glv.config['PANEL_HOST']}{user_data['subscription_url']}"
    await callback_query.message.answer(f"🔗 Ваша подписка: {subscription_url}")
    await callback_query.answer()

# ⚡️ Уведомления об окончании подписки
async def notify_users_about_expiry():
    ONE_DAY = 24 * 3600
    THREE_HOURS = 3 * 3600
    logging.warning("🔥 notify_users_about_expiry() ЗАПУЩЕНА!!!")

    while True:
        users = get_all_users()
        logging.warning(f"🔎 Получено пользователей: {len(users)}")
        now = int(time.time())

        for user in users:
            try:
                vpn_user = await get_vpn_user_by_username(user['username'])
                logging.warning(f"🧠 vpn_user: {vpn_user}")
                logging.warning(f"📆 expire: {vpn_user.expire if vpn_user else 'vpn_user = None'}")

                if not vpn_user or not vpn_user.expire:
                    continue

                time_left = vpn_user.expire - now
                logging.warning(f"👀 Проверяем: {user['username']}, осталось {time_left} секунд")

                if 0 < time_left < ONE_DAY and not user.get('notified_24h'):
                    await bot.send_message(user['telegram_id'], "⚡️ Ваша подписка истекает через 24 часа! Продлите, чтобы избежать отключения.")
                    mark_user_notified(user['telegram_id'], 'notified_24h')
                    logging.info(f"✅ Отправили 24h-уведомление: {user['username']}")

                if 0 < time_left < THREE_HOURS and not user.get('notified_3h'):
                    await bot.send_message(user['telegram_id'], "🚨 Осталось меньше 3 часов до окончания подписки! Поторопитесь с оплатой!")
                    mark_user_notified(user['telegram_id'], 'notified_3h')
                    logging.info(f"✅ Отправили 3h-уведомление: {user['username']}")

            except Exception as e:
                logging.exception(f"❌ Ошибка при уведомлении пользователя {user['telegram_id']}: {e}")

        await asyncio.sleep(3600)


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

    asyncio.create_task(notify_users_about_expiry())
    
    asyncio.create_task(update_panels())

    asyncio.create_task(periodic_restart())


    await asyncio.Event().wait()

async def periodic_restart():
    while True:
        await asyncio.sleep(7320)  # раз в сутки
        logging.info("♻️ Перезапуск бота по таймеру...")
        os._exit(1)  # жёсткий рестарт контейнера, docker его поднимет снова

if __name__ == "__main__":
    asyncio.run(main())
