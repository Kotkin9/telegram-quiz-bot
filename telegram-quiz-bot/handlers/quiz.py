import json
import asyncio
from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import Command
from data.database import get_quiz_index, update_quiz_index, save_result, get_stats, get_top_players

router = Router()
user_states = {}  # {user_id: {'username': str, 'answers': [], 'score': 0}}

with open('data/questions.json', encoding='utf-8') as f:
    quiz_data = json.load(f)

def generate_options_keyboard(options, correct_option):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.add(InlineKeyboardButton(
            text=option,
            callback_data=f"{i}_{correct_option}"
        ))
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз @QuuuiiizBot!", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Anonymous"
    user_states[user_id] = {'username': username, 'answers': [], 'score': 0}
    await update_quiz_index(user_id, 0, 0)
    await message.answer("Давайте начнем квиз!")
    await get_question(message, user_id)

@router.message(F.text == "Начать игру")
async def cmd_start_game(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Anonymous"
    user_states[user_id] = {'username': username, 'answers': [], 'score': 0}
    await update_quiz_index(user_id, 0, 0)
    await message.answer("Давайте начнем квиз!")
    await get_question(message, user_id)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    score, total = await get_stats(user_id)
    await message.answer(f"Ваш последний результат: {score}/{total}")

@router.message(Command("top"))
async def cmd_top(message: Message):
    top_players = await get_top_players(5)
    text = "Топ-5 игроков:\n"
    for i, (username, score, total) in enumerate(top_players, 1):
        text += f"{i}. {username}: {score}/{total}\n"
    await message.answer(text or "Нет результатов.")

async def get_question(message: Message, user_id: int):
    current_index, score = await get_quiz_index(user_id)
    if current_index >= len(quiz_data):
        total = len(quiz_data)
        await save_result(user_id, user_states[user_id]['username'], score, total)
        answers_text = "\n".join(f"Вопрос {i+1}: {ans}" for i, ans in enumerate(user_states[user_id]['answers']))
        await message.answer(
            f"Квиз завершен!\nВаш счет: {score}/{total}\nВаши ответы:\n{answers_text}"
        )
        del user_states[user_id]
        return
    q = quiz_data[current_index]
    keyboard = generate_options_keyboard(q['options'], q['correct_option'])
    await message.answer(f"Вопрос {current_index + 1}/{len(quiz_data)}: {q['question']}", reply_markup=keyboard)

@router.callback_query()
async def answer_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_states:
        await callback.answer("Квиз не активен!")
        return
    current_index, score = await get_quiz_index(user_id)
    if current_index >= len(quiz_data):
        await callback.answer("Квиз завершен!")
        return
    q = quiz_data[current_index]
    answer_index, correct_index = map(int, callback.data.split('_'))
    selected_answer = q['options'][answer_index]
    user_states[user_id]['answers'].append(selected_answer)
    is_correct = answer_index == correct_index
    if is_correct:
        user_states[user_id]['score'] += 1
        score += 1
    await callback.bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    correct_answer = q['options'][correct_index]
    await callback.message.answer(
        f"{'Верно!' if is_correct else f'Неправильно. Правильный: {correct_answer}'}\nВаш выбор: {selected_answer}"
    )
    current_index += 1
    await update_quiz_index(user_id, current_index, score)
    await get_question(callback.message, user_id)
    await callback.answer()