from aiogram.fsm.state import State, StatesGroup


class AI(StatesGroup):
    question = State()
    answer = State()
    disabled = State()
    selecting_model = State()
