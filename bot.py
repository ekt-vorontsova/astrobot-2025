import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from openai import OpenAI

# === Загрузка переменных окружения ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

if not BOT_TOKEN:
    raise RuntimeError("❌ Нет BOT_TOKEN в .env")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ Нет OPENAI_API_KEY в .env")

# === Инициализация клиентов ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    default_headers={
        "HTTP-Referer": "https://t.me/your_bot_username",  # замени на ссылку своего бота
        "X-Title": "AstroBot",
    },
)

user_data = {}  # временное хранилище данных пользователей


# === Функция GPT-запроса ===
async def ask_gpt(prompt: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=60.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка GPT: {e}"


# === Главное меню ===
def main_menu():
    buttons = [
        ["🔮 Гороскоп на сегодня"],
        ["🌟 Совет дня от звёзд"],
        ["✨ Получить персональный прогноз"],
        ["💫 Спросить совета у звёзд"],
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=b) for b in row] for row in buttons],
        resize_keyboard=True
    )


# === /start ===
@dp.message(CommandStart())
async def start(message: types.Message):
    zodiac_buttons = [
        ["♈ Овен", "♉ Телец", "♊ Близнецы"],
        ["♋ Рак", "♌ Лев", "♍ Дева"],
        ["♎ Весы", "♏ Скорпион", "♐ Стрелец"],
        ["♑ Козерог", "♒ Водолей", "♓ Рыбы"],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=b) for b in row] for row in zodiac_buttons],
        resize_keyboard=True
    )
    await message.answer(
        "✨ Привет! Я твой персональный астропомощник.\nВыбери свой знак зодиака:",
        reply_markup=keyboard
    )


# === Выбор знака ===
@dp.message(lambda m: any(z in m.text for z in [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]))
async def choose_zodiac(message: types.Message):
    user_data[message.from_user.id] = {"zodiac": message.text}
    await message.answer(
        f"Отлично, твой знак — {message.text}!\nЧто хочешь узнать?",
        reply_markup=main_menu()
    )


# === Гороскоп на сегодня (со звёздным ожиданием) ===
@dp.message(lambda m: "Гороскоп на сегодня" in m.text)
async def horoscope_today(message: types.Message):
    zodiac = user_data.get(message.from_user.id, {}).get("zodiac", "неизвестен")

    wait_msg = await message.answer("🔭 Звёзды выстраиваются в созвездия…")
    await asyncio.sleep(1.8)
    await wait_msg.edit_text("✨ Смотрим, какие энергии окружают знак…")
    await asyncio.sleep(1.8)
    await wait_msg.edit_text("🌌 Звёзды уже шепчут свой прогноз…")

    prompt = f"Составь позитивный, вдохновляющий гороскоп на сегодня для знака {zodiac}."
    result = await ask_gpt(prompt)

    await wait_msg.edit_text(f"🔮 {zodiac} — твой гороскоп на сегодня:\n\n{result}")
    await message.answer("Хочешь вернуться в меню?", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Вернуться к списку возможностей")]],
        resize_keyboard=True
    ))


# === Совет дня ===
@dp.message(lambda m: "Совет дня" in m.text)
async def daily_advice(message: types.Message):
    zodiac = user_data.get(message.from_user.id, {}).get("zodiac", "неизвестен")

    wait_msg = await message.answer("🔭 Звёзды советуются между собой…")
    await asyncio.sleep(2)
    await wait_msg.edit_text("🌠 Созвездия находят ответ…")

    prompt = f"Дай короткий, вдохновляющий совет дня для знака {zodiac} с мистической ноткой."
    result = await ask_gpt(prompt)

    await wait_msg.edit_text(f"🌟 Совет звёзд для {zodiac}:\n\n{result}")
    await message.answer("Хочешь вернуться в меню?", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Вернуться к списку возможностей")]],
        resize_keyboard=True
    ))


# === Спросить совета у звёзд ===
@dp.message(lambda m: "Спросить совета" in m.text)
async def ask_topic(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    for topic in ["❤️ Любовь", "💼 Бизнес", "🏡 Семья", "💪 Здоровье", "🚀 Карьера"]:
        keyboard.button(text=topic)
    keyboard.adjust(2)
    await message.answer("Выбери, в какой сфере хочешь совета 🌌:", reply_markup=keyboard.as_markup(resize_keyboard=True))


@dp.message(lambda m: any(x in m.text for x in ["Любовь", "Бизнес", "Семья", "Здоровье", "Карьера"]))
async def give_topic_advice(message: types.Message):
    zodiac = user_data.get(message.from_user.id, {}).get("zodiac", "неизвестен")
    topic = message.text.strip().split(" ")[-1]

    wait_msg = await message.answer("✨ Заглядываю в карту звёзд…")
    await asyncio.sleep(1.8)
    await wait_msg.edit_text("🌙 Планеты обсуждают твою судьбу…")

    prompt = f"Дай совет для знака {zodiac} по теме '{topic}', используя астрологические архетипы и позитивный тон."
    result = await ask_gpt(prompt)

    await wait_msg.edit_text(f"💫 Совет звёзд для {zodiac} ({topic}):\n\n{result}")
    await message.answer("Хочешь вернуться в меню?", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Вернуться к списку возможностей")]],
        resize_keyboard=True
    ))


# === Персональный прогноз ===
@dp.message(lambda m: "Получить персональный прогноз" in m.text)
async def ask_personal(message: types.Message):
    await message.answer("✨ Для персонального прогноза мне нужно немного данных.\nКак тебя зовут?")
    user_data[message.from_user.id]["step"] = "name"


@dp.message(lambda m: user_data.get(m.from_user.id, {}).get("step") == "name")
async def get_name(message: types.Message):
    user_data[message.from_user.id]["name"] = message.text
    user_data[message.from_user.id]["step"] = "birth_date"
    await message.answer("📅 Укажи дату рождения (например, 14.10.1995):")


@dp.message(lambda m: user_data.get(m.from_user.id, {}).get("step") == "birth_date")
async def get_birth_date(message: types.Message):
    user_data[message.from_user.id]["birth_date"] = message.text
    user_data[message.from_user.id]["step"] = "birth_time"
    await message.answer("⏰ Введи время рождения (например 15:45):")


@dp.message(lambda m: user_data.get(m.from_user.id, {}).get("step") == "birth_time")
async def get_birth_time(message: types.Message):
    user_data[message.from_user.id]["birth_time"] = message.text
    user_data[message.from_user.id]["step"] = "birth_place"
    await message.answer("🌍 Укажи место рождения (город, страна):")


@dp.message(lambda m: user_data.get(m.from_user.id, {}).get("step") == "birth_place")
async def get_birth_place(message: types.Message):
    info = user_data[message.from_user.id]
    info["birth_place"] = message.text
    user_data[message.from_user.id]["step"] = None

    wait_msg = await message.answer("🪐 Рассчитываю натальную карту…")
    await asyncio.sleep(2)
    await wait_msg.edit_text("🌞 Смотрю, как планеты влияют на судьбу…")

    prompt = (
        f"Составь персональный астрологический прогноз для {info['name']}.\n"
        f"Дата рождения: {info['birth_date']}\n"
        f"Время рождения: {info['birth_time']}\n"
        f"Место рождения: {info['birth_place']}\n"
        "Проанализируй натальную карту и текущие транзиты. Дай доброжелательный, вдохновляющий прогноз."
    )
    result = await ask_gpt(prompt)

    await wait_msg.edit_text(f"🔮 Персональный прогноз для {info['name']}:\n\n{result}")
    await message.answer("Хочешь вернуться в меню?", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Вернуться к списку возможностей")]],
        resize_keyboard=True
    ))


# === Возврат в главное меню ===
@dp.message(lambda m: "Вернуться" in m.text)
async def back_to_menu(message: types.Message):
    zodiac = user_data.get(message.from_user.id, {}).get("zodiac", "друг звёзд")
    await message.answer(f"🔙 Возвращаемся в меню, {zodiac}!", reply_markup=main_menu())


# === Запуск ===
async def main():
    print("🚀 Бот запущен и ждёт звёздных вопросов...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

