import os
import json
import asyncio
import logging
from typing import Dict

from aiogram import Bot, Dispatcher, F, types
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
    raise ValueError("BOT_TOKEN missing in environment variables")

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
    waiting_reply = State()
    waiting_type = State()

class AdminDeleteState(StatesGroup):
    waiting_delete_key = State()

# ================= MENUS =================
def main_menu_kb():
    # Reply buttons (dynamic reply-type buttons)
    reply_rows = []
    for key, val in buttons_data.items():
        if val.get("type") == "reply":
            reply_rows.append([KeyboardButton(val.get("text"))])

    # Static main options
    reply_rows.append([KeyboardButton("📂 Open Menu")])
    reply_rows.append([KeyboardButton("ℹ️ Help")])

    return ReplyKeyboardMarkup(keyboard=reply_rows, resize_keyboard=True)

def inline_dynamic_menu():
    rows = []
    for key, val in buttons_data.items():
        if val.get("type") == "inline":
            rows.append([InlineKeyboardButton(val.get("text"), callback_data=f"dyn_{key}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_panel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Add Button")],
            [KeyboardButton("📋 List Buttons")],
            [KeyboardButton("❌ Delete Button")],
            [KeyboardButton("⬅️ Back")]
        ],
        resize_keyboard=True
    )

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Ku soo dhawoow 🤖\nIsticmaal menu-ga hoose:", reply_markup=main_menu_kb())

# ================= MAIN MENU ACTIONS =================
@dp.message(F.text == "📂 Open Menu")
async def open_inline_menu(msg: Message):
    await msg.answer("Dooro:", reply_markup=inline_dynamic_menu())

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("Main Menu:", reply_markup=main_menu_kb())

@dp.message(F.text == "ℹ️ Help")
async def help_cmd(msg: Message):
    await msg.answer("Haddii aad rabto wax gaar ah, dooro menu-ga.")

# ================= DYNAMIC HANDLER =================
@dp.callback_query(F.data.startswith("dyn_"))
async def dynamic_inline_handler(call: CallbackQuery):
    key = call.data.split("_", 1)[1]
    data = buttons_data.get(key)
    if not data:
        await call.answer("Button lama helin", show_alert=True)
        return
    await call.message.answer(data.get("reply", ""))

@dp.message()
async def dynamic_reply_handler(msg: Message):
    # Check reply-type buttons
    for key, val in buttons_data.items():
        if val.get("type") == "reply" and msg.text == val.get("text"):
            await msg.answer(val.get("reply", ""))
            return

# ================= ADMIN PANEL =================
@dp.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Admin Panel:", reply_markup=admin_panel_kb())

# ---- ADD BUTTON ----
@dp.message(F.text == "➕ Add Button")
async def admin_add(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Qor magaca button-ka:")
    await state.set_state(AdminAddState.waiting_name)

@dp.message(AdminAddState.waiting_name)
async def admin_add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer("Qor jawaabta (reply text):")
    await state.set_state(AdminAddState.waiting_reply)

@dp.message(AdminAddState.waiting_reply)
async def admin_add_reply(msg: Message, state: FSMContext):
    await state.update_data(reply=msg.text.strip())
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("inline")], [KeyboardButton("reply")]],
        resize_keyboard=True
    )
    await msg.answer("Dooro type: inline ama reply", reply_markup=kb)
    await state.set_state(AdminAddState.waiting_type)

@dp.message(AdminAddState.waiting_type)
async def admin_add_type(msg: Message, state: FSMContext):
    t = msg.text.strip().lower()
    if t not in ["inline", "reply"]:
        await msg.answer("Qor inline ama reply")
        return

    data = await state.get_data()
    key = str(len(buttons_data) + 1)

    buttons_data[key] = {
        "text": data["name"],
        "reply": data["reply"],
        "type": t
    }
    save_buttons(buttons_data)

    await msg.answer("✅ Button waa la daray", reply_markup=admin_panel_kb())
    await state.clear()

# ---- LIST BUTTONS ----
@dp.message(F.text == "📋 List Buttons")
async def admin_list(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    if not buttons_data:
        await msg.answer("Button ma jiro")
        return

    text = "Buttons:\n\n"
    for k, v in buttons_data.items():
        text += f"{k}. {v['text']} ({v['type']})\n"
    await msg.answer(text)

# ---- DELETE BUTTON ----
@dp.message(F.text == "❌ Delete Button")
async def admin_delete(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Qor number-ka button-ka aad rabto inaad tirtirto:")
    await state.set_state(AdminDeleteState.waiting_delete_key)

@dp.message(AdminDeleteState.waiting_delete_key)
async def admin_delete_confirm(msg: Message, state: FSMContext):
    key = msg.text.strip()
    if key in buttons_data:
        buttons_data.pop(key)
        save_buttons(buttons_data)
        await msg.answer("🗑️ Waa la tirtiray", reply_markup=admin_panel_kb())
    else:
        await msg.answer("Button lama helin", reply_markup=admin_panel_kb())
    await state.clear()

# ---- BACK TO MAIN ----
@dp.message(F.text == "⬅️ Back")
async def admin_back(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await msg.answer("Main Menu:", reply_markup=main_menu_kb())

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
