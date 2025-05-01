import logging
from aiogram import types, Router, F, Dispatcher
from utils.goods import get, get_callbacks
from utils.yookassa import create_payment as yk_create_payment
from keyboards.pay import get_pay_keyboard
from app.database import get_user
import glv

router = Router(name="callbacks-router") 

@router.callback_query(lambda c: c.data in get_callbacks())
async def process_buy_subscription(callback_query: types.CallbackQuery):
    try:
        good = get(callback=callback_query.data)
        if not good:
            await callback_query.answer("❌ Товар не найден.", show_alert=True)
            return

        # ??????? ???????????? ?? Telegram ID
        user_data = get_user(callback_query.from_user.id)
        if not user_data:
            await callback_query.answer("❌ Вы не зарегистрированы. Нажмите /start.", show_alert=True)
            return

        # Email 
        email = user_data.get('email') or "admin@shadowpathrt.ru"

        # ?????????? ??????
        payment = await yk_create_payment(
            tg_id=callback_query.from_user.id,
            callback=callback_query.data,
            email=email,
            chat_id=callback_query.message.chat.id,
            lang_code=callback_query.from_user.language_code
        )

        # ?????????? ????????? ? ??????? ????????
        await callback_query.message.answer(
            f"Сумма к оплате: {payment['amount']}?\n"
            f"Нажмите кнопку ниже для оплаты:",
            reply_markup=get_pay_keyboard(payment["url"])
        )

        await callback_query.answer()

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке покупки: {e}")
        await callback_query.answer("Произошла ошибка при обработке платежа.", show_alert=True)

def register_callbacks(dp: Dispatcher):
    dp.include_router(router)
