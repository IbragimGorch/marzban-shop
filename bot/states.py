from aiogram.fsm.state import State, StatesGroup

class SerialState(StatesGroup):
    waiting_for_serial = State()

class EmailState(StatesGroup):
    waiting_for_email = State()
