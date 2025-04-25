from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from utils.goods import get as get_good
from utils.yookassa import create_payment

from keyboards import get_payment_keyboard, get_pay_keyboard
from utils import goods, yookassa, cryptomus

router = Router(name="callbacks-router") 

@router.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery):
    await callback.message.delete()
    code = callback.data.split("_", 1)[1]  # e.g. 'month1'
    good = get_good(code)
    if not good:
        return await callback.answer()
    # create payment
    result = await create_payment(
        callback.from_user.id,
        code,
        callback.message.chat.id,
        callback.from_user.language_code
    )
    # send payment link
    await callback.message.answer(
        f"Перейдите по ссылке для оплаты ({good['title']}):\n{result['url']}"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data in goods.get_callbacks())
async def callback_payment_method_select(callback: CallbackQuery):
    await callback.message.delete()
    good = goods.get(callback.data)
    await callback.message.answer(text=_("Select payment method ⬇️"), reply_markup=get_payment_keyboard(good))
    await callback.answer()

def register_callbacks(dp: Dispatcher):
    dp.include_router(router)
