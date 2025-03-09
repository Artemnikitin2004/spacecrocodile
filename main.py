import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Твой токен бота
TOKEN = "7639487696:AAF_thNH2X320VRxBb2he8iot2UhyA8i5Xg"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояние активных игр
active_games = {}

# Функция загрузки слов из файла
def load_words(filename="words.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        return ["старшип", "маск", "ракета", "луна", "марс"]  # Запасной список слов

words_list = load_words()

# Функция выбора случайного слова
def get_random_word(exclude_word=None):
    available_words = [word for word in words_list if word != exclude_word]
    return random.choice(available_words) if available_words else None

# Команда /startnewgame
@dp.message(Command("startnewgame"))
async def start_new_game(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.full_name

    if chat_id in active_games:
        await message.answer("Игра уже идёт. Завершите её, чтобы начать новую.")
        return

    word = get_random_word()
    if not word:
        await message.answer("Ошибка: нет слов в базе!")
        return

    active_games[chat_id] = {
        "host": user_id,
        "host_name": username,
        "word": word
    }

    await message.answer(f"Игра началась. Ведущий: <b>{username}</b>")

    # Кнопки для ведущего
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{word}")],
        [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
    ])

    await message.answer(f"<b>{username}</b>, нажмите кнопку ниже, чтобы увидеть слово!", reply_markup=keyboard)

# Обработчик кнопки "Показать слово"
@dp.callback_query(lambda c: c.data.startswith("show_word:"))
async def show_word(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in active_games or active_games[chat_id]["host"] != user_id:
        await callback_query.answer("Вы не ведущий!", show_alert=True)
        return

    word = active_games[chat_id]["word"]
    await callback_query.answer(f"Ваше слово: {word}", show_alert=True)

# Обработчик кнопки "Пропустить слово"
@dp.callback_query(lambda c: c.data == "skip_word")
async def skip_word(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in active_games or active_games[chat_id]["host"] != user_id:
        await callback_query.answer("Вы не ведущий!", show_alert=True)
        return

    new_word = get_random_word(exclude_word=active_games[chat_id]["word"])
    if not new_word:
        await callback_query.answer("Ошибка: нет других слов в базе!", show_alert=True)
        return

    active_games[chat_id]["word"] = new_word
    await callback_query.message.edit_text(f"Слово обновлено. Нажмите кнопку ниже, чтобы увидеть его.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{new_word}")],
        [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
    ]))
    await callback_query.answer("Слово обновлено!")

# Проверка правильности ответа
async def check_word(message: types.Message):
    """Проверяет правильность ответа в группе"""
    if message.chat.type not in ["group", "supergroup"]:
        return  # Игнорируем ЛС

    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.full_name

    if not message.text:
        return

    text = message.text.strip().lower()  # Приводим к нижнему регистру
    print(f"[DEBUG] Получено сообщение из чата {chat_id}: {text}")

    if chat_id not in active_games:
        return

    game = active_games[chat_id]
    correct_word = game["word"]
    print(f"[DEBUG] Ожидаемое слово: {correct_word}")

    if text == correct_word:  # Проверяем, совпадает ли слово
        await message.answer(f"Игрок <b>{username}</b> угадал слово <b>{text}</b> и теперь является ведущим!")

        new_word = get_random_word()
        if not new_word:
            await message.answer("Ошибка: нет слов в базе!")
            return

        active_games[chat_id] = {
            "host": user_id,
            "host_name": username,
            "word": new_word
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{new_word}")],
            [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
        ])

        await message.answer(f"<b>{username}</b>, нажмите кнопку ниже, чтобы увидеть слово!", reply_markup=keyboard)
    else:
        print("[DEBUG] Слово не совпало.")

# Команда /stopgame
@dp.message(Command("stopgame"))
async def stop_game(message: types.Message):
    chat_id = message.chat.id

    if chat_id in active_games:
        del active_games[chat_id]
        await message.answer("Игра окончена. Чтобы сыграть снова, введите команду /startnewgame")
        print(f"[DEBUG] Игра в чате {chat_id} завершена.")
    else:
        await message.answer("Сейчас нет активной игры.")

# Запуск бота
async def main():
    print("[DEBUG] Бот запущен...")

    # Регистрируем обработчик сообщений
    dp.message.register(check_word)  # Теперь бот обрабатывает сообщения в группах

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Твой токен бота
TOKEN = "7639487696:AAF_thNH2X320VRxBb2he8iot2UhyA8i5Xg"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояние активных игр
active_games = {}

# Функция загрузки слов из файла
def load_words(filename="words.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        return ["старшип", "маск", "ракета", "луна", "марс"]  # Запасной список слов

words_list = load_words()

# Функция выбора случайного слова
def get_random_word(exclude_word=None):
    available_words = [word for word in words_list if word != exclude_word]
    return random.choice(available_words) if available_words else None

# Команда /startnewgame
@dp.message(Command("startnewgame"))
async def start_new_game(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.full_name

    if chat_id in active_games:
        await message.answer("Игра уже идёт. Завершите её, чтобы начать новую.")
        return

    word = get_random_word()
    if not word:
        await message.answer("Ошибка: нет слов в базе!")
        return

    active_games[chat_id] = {
        "host": user_id,
        "host_name": username,
        "word": word
    }

    await message.answer(f"Игра началась. Ведущий: <b>{username}</b>")

    # Кнопки для ведущего
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{word}")],
        [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
    ])

    await message.answer(f"<b>{username}</b>, нажмите кнопку ниже, чтобы увидеть слово!", reply_markup=keyboard)

# Обработчик кнопки "Показать слово"
@dp.callback_query(lambda c: c.data.startswith("show_word:"))
async def show_word(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in active_games or active_games[chat_id]["host"] != user_id:
        await callback_query.answer("Вы не ведущий!", show_alert=True)
        return

    word = active_games[chat_id]["word"]
    await callback_query.answer(f"Ваше слово: {word}", show_alert=True)

# Обработчик кнопки "Пропустить слово"
@dp.callback_query(lambda c: c.data == "skip_word")
async def skip_word(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in active_games or active_games[chat_id]["host"] != user_id:
        await callback_query.answer("Вы не ведущий!", show_alert=True)
        return

    new_word = get_random_word(exclude_word=active_games[chat_id]["word"])
    if not new_word:
        await callback_query.answer("Ошибка: нет других слов в базе!", show_alert=True)
        return

    active_games[chat_id]["word"] = new_word
    await callback_query.message.edit_text(f"Слово обновлено. Нажмите кнопку ниже, чтобы увидеть его.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{new_word}")],
        [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
    ]))
    await callback_query.answer("Слово обновлено!")

# Проверка правильности ответа
async def check_word(message: types.Message):
    """Проверяет правильность ответа в группе"""
    if message.chat.type not in ["group", "supergroup"]:
        return  # Игнорируем ЛС

    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.full_name

    if not message.text:
        return

    text = message.text.strip().lower()  # Приводим к нижнему регистру
    print(f"[DEBUG] Получено сообщение из чата {chat_id}: {text}")

    if chat_id not in active_games:
        return

    game = active_games[chat_id]
    correct_word = game["word"]
    print(f"[DEBUG] Ожидаемое слово: {correct_word}")

    if text == correct_word:  # Проверяем, совпадает ли слово
        await message.answer(f"Игрок <b>{username}</b> угадал слово <b>{text}</b> и теперь является ведущим!")

        new_word = get_random_word()
        if not new_word:
            await message.answer("Ошибка: нет слов в базе!")
            return

        active_games[chat_id] = {
            "host": user_id,
            "host_name": username,
            "word": new_word
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать слово", callback_data=f"show_word:{new_word}")],
            [InlineKeyboardButton(text="Пропустить слово", callback_data="skip_word")]
        ])

        await message.answer(f"<b>{username}</b>, нажмите кнопку ниже, чтобы увидеть слово!", reply_markup=keyboard)
    else:
        print("[DEBUG] Слово не совпало.")

# Команда /stopgame
@dp.message(Command("stopgame"))
async def stop_game(message: types.Message):
    chat_id = message.chat.id

    if chat_id in active_games:
        del active_games[chat_id]
        await message.answer("Игра окончена. Чтобы сыграть снова, введите команду /startnewgame")
        print(f"[DEBUG] Игра в чате {chat_id} завершена.")
    else:
        await message.answer("Сейчас нет активной игры.")

# Запуск бота
async def main():
    print("[DEBUG] Бот запущен...")

    # Регистрируем обработчик сообщений
    dp.message.register(check_word)  # Теперь бот обрабатывает сообщения в группах

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
