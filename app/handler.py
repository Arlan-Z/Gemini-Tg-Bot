from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from app.states import AI
from config import AI_TOKEN

import google.generativeai as genai

router = Router()
genai.configure(api_key=AI_TOKEN)


def get_model_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Gemini 1.5 Flash", callback_data="gemini-1.5-flash")],
        [InlineKeyboardButton(text="Gemini 1.5 Pro", callback_data="gemini-1.5-pro")]
    ])
    return keyboard


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer('Gemini 1.5 Flash: Быстрые ответы, но не точные\nGemini 1.5 Pro: Более точные, но более медленный', reply_markup=get_model_keyboard())
    #await message.answer('Выберите модель:', reply_markup=get_model_keyboard())
    await state.set_state(AI.selecting_model)


@router.message(Command('stop'))
async def cmd_stop(message: Message, state: FSMContext):
    await state.set_state(AI.disabled)
    await message.answer('Бот отключен. Используйте /start для повторного включения.')


@router.callback_query(lambda c: c.data in ["gemini-1.5-flash", "gemini-1.5-pro"])
async def select_model(callback: CallbackQuery, state: FSMContext):
    selected_model = callback.data
    await state.update_data(selected_model=selected_model)
    await callback.message.answer(f"Вы выбрали {selected_model}. Теперь вы можете начать диалог.")
    await state.set_state(AI.question)
    await callback.answer()


@router.message(F.text)
async def ai(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AI.disabled.state:
        await message.answer('Бот отключен. Используйте /start для повторного включения.')
        return

    data = await state.get_data()
    selected_model = data.get('selected_model')

    model = genai.GenerativeModel(selected_model)

    await state.set_state(AI.answer)
    try:
        chat = data.get('context')
        if not chat:
            chat = model.start_chat(history=[])

        if len(chat.history) > 10:
            chat = model.start_chat(history=[])

        response = await chat.send_message_async(message.text)
        data['context'] = chat
        await state.update_data(data)

    except Exception as e:
        print(e)
        chat = model.start_chat(history=[])
        response = await chat.send_message_async(message.text)
        await state.update_data({'context': chat})

    await message.answer(response.text, parse_mode='Markdown')
    await state.set_state(AI.question)
