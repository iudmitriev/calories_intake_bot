from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp

from food_info import calculate_water, get_food_info, calculate_calories, get_calories_burned
from states import Form, LogCalories


router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настроить профиль пользователя\n"
    )

# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(age=float(message.text))
    await message.reply("Введите ваш город:")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_activity_level(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity_level)

@router.message(Form.activity_level)
async def process_сalories_target(message: Message, state: FSMContext):
    await state.update_data(activity_level=float(message.text))

    data = await state.get_data()
    calories = calculate_calories(
        weight=data.get("weight"),
        height=data.get("height"), 
        age=data.get("age"),
        activity_level=data.get("activity_level")
    )
    await state.update_data(calories_goal=calories)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Да"),
                KeyboardButton(text="Нет"),
            ]
        ],
        resize_keyboard=True,
    )
    await message.reply(f"Рекомендованное число калорий - {calories}. Хотите его изменить?", reply_markup=keyboard)
    await state.set_state(Form.calories_change_request)

@router.message(Form.calories_change_request, F.text.casefold() == "нет")
async def accept_calories(message: Message, state: FSMContext):
    await message.reply("Ваши данные сохранены!", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.finished)


@router.message(Form.calories_change_request, F.text.casefold() == "да")
async def request_calories_change(message: Message, state: FSMContext):
    await message.reply("Какое число калорий вы хотите тратить в день?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.changing_calories)

@router.message(Form.changing_calories)
async def changing_calories(message: Message, state: FSMContext):
    await state.update_data(calories=float(message.text))
    await message.reply("Ваши данные сохранены!")
    await state.set_state(Form.finished)

@router.message(Command("get_calories"))
async def start_form(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.reply(f"Ваша норма - {data.get('calories_goal')} калорий")

@router.message(Command("log_water"))
async def log_water(message: Message, state: FSMContext):
    data = await state.get_data()
    water_norm = await calculate_water(
        weight=data.get("weight"),
        activity_level=data.get("activity_level"),
        city=data.get("city")
    )
    current_water_consumption = data.get("current_water_consumption", 0)
    current_water_consumption += float(message.text.removeprefix('/log_water '))
    await state.update_data(current_water_consumption=current_water_consumption)
    await message.reply(f"За сегодня вы выпили {current_water_consumption} из {water_norm} мл воды")

@router.message(Command("log_calories"))
async def log_calories_product(message: Message, state: FSMContext):
    calories_consumed_by_100g = await get_food_info(
        product_name=message.text.removeprefix('/log_calories ')
    )
    if calories_consumed_by_100g is not None:
        await state.update_data(current_product_calories=calories_consumed_by_100g)
    await message.reply("Сколько грамм вы съели?")
    await state.set_state(LogCalories.request_quantity)

@router.message(LogCalories.request_quantity)
async def log_calories_amount(message: Message, state: FSMContext):
    amount = float(message.text)
    data = await state.get_data()

    calories_consumption = data.get("calories_consumption", 0)
    consumed = data.get("current_product_calories", 0) * amount / 100
    calories_consumption += consumed
    await state.update_data(calories_consumption=calories_consumption)
    await message.reply(f"Записано: {consumed} ккал.")
    await state.set_state(LogCalories.finished)

@router.message(Command("log_workout"))
async def log_workout(message: Message, state: FSMContext):
    data = await state.get_data()
    burned_calories = await get_calories_burned(
        description=message.text.removeprefix('/log_workout '), 
        weight=data.get('weight', 75)
    )
    total_burned_calories = data.get("total_burned_calories", 0)
    total_burned_calories += burned_calories
    await state.update_data(total_burned_calories=total_burned_calories)
    await message.reply(f"Вы сожгли {burned_calories} ккал.")


@router.message(Command("check_progress"))
async def check_progress(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("weight"):
        msg = "Для просмотра прогресса необходимо заполнить информацию о себе при помощи /set_profile"
        await message.reply(msg)
        return


    water_norm = await calculate_water(
        weight=data.get("weight"),
        activity_level=data.get("activity_level"),
        city=data.get("city")
    )
    current_water_consumption = data.get("current_water_consumption", 0)

    calories_consumption = data.get("calories_consumption", 0)
    total_burned_calories = data.get("total_burned_calories", 0)
    calories_goal = data.get("calories_goal", 0)
    msg = f"""📊 Прогресс:
    Вода:
    - Выпито: {current_water_consumption} мл из {water_norm} мл.
    - Осталось: {max(0, water_norm - current_water_consumption)} мл.
    
    Калории:
    - Потреблено: {calories_consumption} ккал из {calories_goal} ккал.
    - Сожжено: {total_burned_calories} ккал.
    - Баланс: {calories_consumption - total_burned_calories} ккал.
    """
    await message.reply(msg)


# Получение шутки из API
@router.message(Command("joke"))
async def get_joke(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.chucknorris.io/jokes/random") as response:
            joke = await response.json()
            await message.reply(joke["value"])

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
