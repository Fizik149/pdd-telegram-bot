import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
import json
from datetime import datetime, timedelta

BOT_TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

class QuizStates(StatesGroup):
    quiz = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Введите /activate чтобы активировать код.")

@router.message(F.text == "/menu")
async def cmd_menu(message: Message):
    await message.answer("📋 Главное меню:
/activate - Ввести код
/quiz - Начать викторину
/restart - Сбросить викторину")

@router.message(F.text == "/restart")
async def cmd_restart(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Викторина сброшена. Введите /quiz чтобы начать заново.")

@router.message(F.text == "/activate")
async def cmd_activate(message: Message, state: FSMContext):
    await message.answer("🔑 Введите ваш код активации:")
    await state.set_state("waiting_for_code")

@router.message(F.text == "/quiz")
async def cmd_quiz(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    with open("codes.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if user_id not in data["users"]:
        await message.answer("❗️Сначала активируйте код через /activate")
        return

    user = data["users"][user_id]
    if datetime.strptime(user["expires"], "%Y-%m-%d") < datetime.now():
        await message.answer("⏳ Срок действия кода истёк.")
        return

    user["current_question"] = 0
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    await send_question(message.chat.id, user_id)

async def send_question(chat_id, user_id):
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open("codes.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    user = data["users"][user_id]
    q_index = user.get("current_question", 0)

    if q_index >= len(questions):
        await bot.send_message(chat_id, "🎉 Викторина завершена!")
        return

    question = questions[q_index]
    options = question["options"]
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data=f"answer:{i}")]
        for i, opt in enumerate(options)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, f"❓ {question['text']}", reply_markup=markup)

@router.message(F.state == "waiting_for_code")
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = str(message.from_user.id)
    with open("codes.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if code in data["codes"] and data["codes"][code]["active"] and not data["codes"][code]["used"]:
        data["codes"][code]["used"] = True
        data["codes"][code]["used_by"] = user_id
        data["codes"][code]["used_at"] = datetime.now().strftime("%Y-%m-%d")
        data["users"][user_id] = {
            "activated": datetime.now().strftime("%Y-%m-%d"),
            "expires": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "current_question": 0
        }
        with open("codes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        await message.answer("✅ Код активирован! Теперь можете пройти /quiz.")
    else:
        await message.answer("❌ Неверный или уже использованный код.")
    await state.clear()

@router.callback_query(F.data.startswith("answer:"))
async def handle_answer(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    user_id = str(callback.from_user.id)
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open("codes.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    q_index = data["users"][user_id]["current_question"]
    question = questions[q_index]
    correct = question["correct_option"]

    if index == correct:
        await callback.message.answer("✅ Верно!")
    else:
        await callback.message.answer(f"❌ Неверно. Правильный ответ: {question['options'][correct]}")

    data["users"][user_id]["current_question"] += 1
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    await send_question(callback.message.chat.id, user_id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
