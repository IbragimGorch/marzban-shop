from yookassa import Configuration, Payment
from db.methods import add_yookassa_payment
from utils import goods
import glv
import logging


shop_id = glv.config['YOOKASSA_SHOPID']
secret_key = glv.config['YOOKASSA_TOKEN']
logging.info(f"→ YooKassa.configure(shop_id={shop_id!r}, secret={'***' if secret_key else None})")
Configuration.configure(shop_id, secret_key)

async def create_payment(tg_id: int,
                         callback: str,
                         chat_id: int,
                         lang_code: str,
                         email: str 
                        ) -> dict:
    """
    Создает платёж в YooKassa, сохраняет его в БД и возвращает сумму и ссылку для оплаты.
    Если указан email, добавляет чек с email покупателя.
    """
    good = goods.get(callback)

        # build a static return_url once
    bot_user = await glv.bot.get_me()
    return_url = f"https://t.me/{bot_user.username}"

    # create a new payment
    payment = Payment.create({
        "amount": {
            "value":    str(good['price']['ru']),  # must be a string
            "currency": "RUB"
        },
        "confirmation": {
            "type":       "redirect",
            "return_url": return_url
        },
        "capture":  True,
        "description": f"Подписка на VPN {glv.config['SHOP_NAME']}",
        "save_payment_method": False,
        "receipt": {
            "customer": {"email": email},
            "items": [{
                "description": f"{good['months']} мес. подписка",
                "quantity":    "1",
                "amount": {
                    "value":    str(good['price']['ru']),
                    "currency": "RUB"
                },
                "vat_code": "1"
            }]
        }
    })

    # persist to your DB
    await add_yookassa_payment(
        tg_id=tg_id,
        callback=callback,
        chat_id=chat_id,
        lang_code=lang_code,
        payment_id=payment.id
    )

    # return exactly what your handlers need
    return {
        "amount": payment.amount.value,
        "url":    payment.confirmation.confirmation_url
    }