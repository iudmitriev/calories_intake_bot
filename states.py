from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    weight = State()
    height = State()
    age = State()
    city = State()
    activity_level = State()
    calories_change_request = State()
    changing_calories = State()
    finished = State()

class LogCalories(StatesGroup):
    request_quantity = State()
    finished = State()
