import os
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7983838654"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STORAGE =================
users = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother_name = State()
    photo = State()

class CodeState(StatesGroup):
    code = State()

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4,9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order"),
             KeyboardButton(text="Code Check")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Bot-ka 🤖", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_whatsapp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_tiktok")],
        [InlineKeyboardButton(text="Google", callback_data="v_google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_number(call: CallbackQuery):
    number = normal_number()
    await call.message.edit_text(
        f"Virtual Number ✅\nPlatform: {call.data[2:].capitalize()}\nNumber: {number}"
    )

# ================= CARD =================
@dp.callback_query(F.data == "card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    level = call.data
    number = vip_number() if level=="vip" else normal_number()

    users[call.from_user.id] = {
        "type":"card",
        "level":level,
        "number":number
    }

    await call.message.answer("Fadlan geli Magacaaga Saddexan:")
    await state.set_state(CardState.full_name)

# ================= COLLECT DATA =================
@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    if len(msg.text.split()) < 3:
        await msg.answer("Magac saddexan geli.")
        return
    users[msg.from_user.id]["full_name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother_name)

@dp.message(CardState.mother_name)
async def get_mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga (Toosan):")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    photo = msg.photo[-1].file_id
    users[msg.from_user.id]["photo"] = photo

    data = users[msg.from_user.id]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"approve_{msg.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{msg.from_user.id}")]
    ])

    await bot.send_photo(
        ADMIN_ID,
        photo,
        caption=(
            f"Card Request\n"
            f"Name: {data['full_name']}\n"
            f"Mother: {data['mother']}\n"
            f"Level: {data['level']}"
        ),
        reply_markup=kb
    )

    await msg.answer("Codsigaaga waa la diray ⏳")
    await state.clear()

# ================= ADMIN =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    code = generate_code()
    users[uid]["code"] = code
    await bot.send_message(uid, f"Card Approved ✅\nYour Code: {code}")
    await call.message.edit_caption("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "Card Rejected ❌")
    await call.message.edit_caption("Rejected ❌")

# ================= CODE CHECK =================
@dp.message(F.text == "Code Check")
async def code_check(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-ka:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def verify(msg: Message, state: FSMContext):
    data = users.get(msg.from_user.id)

    if not data or data.get("type") != "card":
        await msg.answer("Ma lihid Card la ansixiyay ❌")
        await state.clear()
        return

    if msg.text == data.get("code"):
        await msg.answer(f"Number-kaaga:\n{data['number']}")
    else:
        await msg.answer("Code khaldan ❌")

    await state.clear()

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
