from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import goods

def get_plans_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с тарифами. В callback_data кладём 'plan:<callback>'.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for g in goods.get():  # список товаров
        title = g.get("title", g.get("callback", "plan"))
        cb = g.get("callback")
        if not cb:
            continue
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=title, callback_data=f"plan:{cb}")
        ])
    return kb
