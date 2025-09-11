import logging
import ipaddress
from aiohttp import web
from aiohttp.web_request import Request
from datetime import datetime

import glv
from utils import goods, marzban_api
from utils.lang import get_i18n_string
from keyboards.main_menu import get_main_menu_keyboard
from db.methods import get_yookassa_payment, delete_payment
from utils.marzban_api import (
    get_marzban_profile, generate_marzban_subscription, generate_subscription_link, extend_user_expire
)
from app.database import get_user, reset_user_notifications, get_telegram_id_by_username


YOOKASSA_IPS = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
]

async def check_yookassa_payment(request: Request):
    logging.info("YooKassa webhook received: %s", await request.text())
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    f = True
    for subnet in YOOKASSA_IPS:
        if "/" in subnet:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(subnet):
                f = False
                break
        else:
            if client_ip == subnet:
                f = False
                break
    if f:
        return web.Response(status=403)
    data = (await request.json())['object']
    payment = await get_yookassa_payment(data['id'])
    if payment == None:
        return web.Response()
    if data['status'] == 'succeeded':
        await delete_payment(payment.payment_id)
        reset_user_notifications(payment.tg_id)

        good = goods.get(payment.callback)
        telegram_user = get_user(payment.tg_id)
        if not telegram_user:
            raise Exception("Telegram user not found")

        username = telegram_user["username"]
        tg_id = telegram_user["telegram_id"]

        # 1) Генерим новую ссылку (без нодов) и сохраняем в telegram_users
        full_url = await generate_subscription_link(username)
        from db.methods import update_telegram_user_subscription
        await update_telegram_user_subscription(tg_id, username, full_url)

        months = int(good.get("months", 1))
        new_expire = await extend_user_expire(username, months)

        # 2) Формируем текст один раз
        text = get_i18n_string(
            "Thank you for your choice ❤️\n\n"
            "<a href=\"{link}\">Subscribe</a> so you don't miss any announcements ✅\n\n"
            "Your subscription is purchased and available in \"My subscription 👤\".",
            payment.lang
        )

        # 3) Шлём сообщение с новой ссылкой
        await glv.bot.send_message(
            payment.chat_id,
            text.format(link=full_url),
            reply_markup=get_main_menu_keyboard(payment.lang)
        )
        return web.Response(status=200)

    #if payment and payment.chat_id:
    #    try:
    #        new_expire_date = datetime.fromtimestamp(user['expire'])
    #        await glv.bot.send_message(
    #            payment.chat_id,
    #            f"✅ {bold('Подписка продлена!')}\n"
    #            f"Теперь активна до: {new_expire_date.strftime('%d.%m.%Y %H:%M')}"
    #        )
    #    except Exception as e:
    #        logging.error(f"Ошибка отправки уведомления о продлении: {e}")
