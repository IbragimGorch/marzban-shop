from yookassa import Configuration, Payment
from db.methods import add_yookassa_payment
from utils import goods
import glv
import logging
from typing import Optional, Dict, Any

shop_id = glv.config['YOOKASSA_SHOPID']
secret_key = glv.config['YOOKASSA_TOKEN']
logging.info(f"→ YooKassa.configure(shop_id={shop_id!r}, secret={'***' if secret_key else None})")
Configuration.configure(shop_id, secret_key)

async def create_payment(
    tg_id: int,
    callback: str,
    chat_id: int,
    lang_code: str,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создаёт платёж в YooKassa, сохраняет его в БД и возвращает сумму и ссылку.
    Если указан email — добавляет чек с email покупателя.
    """
    good = goods.get(callback)
    if not good:
        available = goods.get_callbacks()
        msg = f"Unknown product callback: {callback}. Available: {available}"
        logging.error(f"❌ {msg}")
        raise ValueError(msg)

    logging.info(f"👉 create_payment: callback={callback} good={good}")

    # достаём цену
    try:
        price_ru = good["price"]["ru"]
        amount_str = str(price_ru)  # API требует строку
    except Exception as e:
        logging.exception(f"❌ Bad good format for '{callback}': {good}")
        raise ValueError(f"Bad good format for '{callback}': missing price['ru']") from e

    months = good.get("months", "?")

    # redirect назад в бот
    bot_user = await glv.bot.get_me()
    return_url = f"https://t.me/{bot_user.username}"

    payload: Dict[str, Any] = {
        "amount": {"value": amount_str, "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": return_url},
        "capture": True,
        "description": f"Подписка на VPN {glv.config['SHOP_NAME']}",
        "save_payment_method": False,
    }

    # чек только при наличии email
    if email:
        payload["receipt"] = {
            "customer": {"email": email},
            "items": [{
                "description": f"{months} мес. подписка",
                "quantity": "1",
                "amount": {"value": amount_str, "currency": "RUB"},
                "vat_code": "1"
            }]
        }

    payment = Payment.create(payload)

    # сохраняем в БД запись о платеже
    await add_yookassa_payment(
        tg_id=tg_id,
        callback=callback,
        chat_id=chat_id,
        lang_code=lang_code,
        payment_id=payment.id
    )

    return {
        "amount": payment.amount.value,
        "url": payment.confirmation.confirmation_url
    }
