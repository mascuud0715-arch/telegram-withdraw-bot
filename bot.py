import os
import json
import asyncio
import logging
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654
DATA_FILE = "buttons.json"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing in Railway Variables")

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STORAGE =================
def load_buttons() -> Dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_buttons(data: Dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

buttons_data = load_buttons()

# ================= STATES =================
class AdminAddState(StatesGroup):
    waiting_name = State()
    waiting_type = State()
    waiting_animation = State()
    waiting_animation_type = State()
    waiting_reply = State()

# ================= ANIMATIONS =================
async def countdown_animation(message, seconds=5):
    msg = await message.answer("Starting...")
    for i in range(seconds, 0, -1):
        await msg.edit_text(f"⏳ {i}")
        await asyncio.sleep(1)

async def dots_animation(message):
    msg = await message.answer("Processing")
    for _ in range(5):
        for dots in ["•", "••", "•••", "••••"]:
            await msg.edit_text(f"Processing {dots}")
            await asyncio.sleep(0.5)

async def spinner_animation(message):
    msg = await message.answer("Processing...")
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(20):
        await msg.edit_text(f"{frames[i % len(frames)]} Processing...")
        await asyncio.sleep(0.2)

# ================= MENUS =================
def main_menu_kb():
    rows = []
    for key, val in buttons_data.items():
        if val["type"] == "reply":
            rows.append([KeyboardButton(val["text"])])
    rows.append([KeyboardButton("📂 Open Menu")])
    rows.append([KeyboardButton("ℹ️ Help")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def inline_menu():
    rows = []
    for key, val in buttons_data.items():
        if val["type"] == "inline":
            rows.append([InlineKeyboardButton(val["text"], callback_data=f"dyn_{key}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_panel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Add Button")],
            [KeyboardButton("📋 List Buttons")],
            [KeyboardButton("⬅️ Back")]
        ],
        resize_keyboard=True
    )

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Main Menu:", reply_markup=main_menu_kb())

# ================= MAIN =================
@dp.message(F.text == "📂 Open Menu")
async def open_menu(msg: Message):
    await msg.answer("Dooro:", reply_markup=inline_menu())

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("Main Menu:", reply_markup=main_menu_kb())

# ================= DYNAMIC =================
@dp.callback_query(F.data.startswith("dyn_"))
async def dynamic_handler(call: CallbackQuery):
    key = call.data.split("_")[1]
    data = buttons_data.get(key)
    if not data:
        return

    animation = data.get("animation")

    if animation == "countdown":
        await countdown_animation(call.message)
    elif animation == "dots":
        await dots_animation(call.message)
    elif animation == "spinner":
        await spinner_animation(call.message)

    await call.message.answer(data["reply"])

@dp.message()
async def reply_dynamic(msg: Message):
    for key, val in buttons_data.items():
        if val["type"] == "reply" and msg.text == val["text"]:
            animation = val.get("animation")
            if animation == "countdown":
                await countdown_animation(msg)
            elif animation == "dots":
                await dots_animation(msg)
            elif animation == "spinner":
                await spinner_animation(msg)
            await msg.answer(val["reply"])
            return

# ================= ADMIN =================
@dp.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Admin Panel:", reply_markup=admin_panel_kb())

@dp.message(F.text == "➕ Add Button")
async def add_button(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Magaca button-ka?")
    await state.set_state(AdminAddState.waiting_name)

@dp.message(AdminAddState.waiting_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Type? inline ama reply")
    await state.set_state(AdminAddState.waiting_type)

@dp.message(AdminAddState.waiting_type)
async def get_type(msg: Message, state: FSMContext):
    await state.update_data(type=msg.text.lower())
    await msg.answer("Animation? haa/maya")
    await state.set_state(AdminAddState.waiting_animation)

@dp.message(AdminAddState.waiting_animation)
async def ask_anim(msg: Message, state: FSMContext):
    if msg.text.lower() == "haa":
        await msg.answer("Dooro: countdown / dots / spinner")
        await state.set_state(AdminAddState.waiting_animation_type)
    else:
        await state.update_data(animation=None)
        await msg.answer("Qor reply text:")
        await state.set_state(AdminAddState.waiting_reply)

@dp.message(AdminAddState.waiting_animation_type)
async def save_anim_type(msg: Message, state: FSMContext):
    await state.update_data(animation=msg.text.lower())
    await msg.answer("Qor reply text:")
    await state.set_state(AdminAddState.waiting_reply)

@dp.message(AdminAddState.waiting_reply)
async def save_button(msg: Message, state: FSMContext):
    data = await state.get_data()
    key = str(len(buttons_data) + 1)

    buttons_data[key] = {
        "text": data["name"],
        "reply": msg.text,
        "type": data["type"],
        "animation": data.get("animation")
    }

    save_buttons(buttons_data)

    await msg.answer("✅ Button waa la daray", reply_markup=admin_panel_kb())
    await state.clear()

@dp.message(F.text == "⬅️ Back")
async def back_admin(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Main Menu:", reply_markup=main_menu_kb())

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
