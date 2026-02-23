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
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    photo = State()

class CodeState(StatesGroup):
    code = State()

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4,9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

async def animation(msg, text, sec=5):
    for i in range(sec):
        dots = "." * ((i % 4) + 1)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order"),
                   KeyboardButton(text="Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Bot 🤖", reply_markup=kb)

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
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton(text="Google", callback_data="v_Google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_flow(call: CallbackQuery):
    platform = call.data.split("_")[1]
    number = normal_number()
    code = generate_code()

    users[call.from_user.id] = {
        "type": "virtual",
        "number": number,
        "code": code
    }

    msg = await call.message.edit_text("OTP Searching")
    await animation(msg, "OTP Searching", 5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"Virtual Request\nUser: {call.from_user.id}\nPlatform: {platform}",
        reply_markup=kb
    )

    await msg.edit_text("Codsiga waa la diray ⏳")

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
    number = vip_number() if call.data=="vip" else normal_number()

    users[call.from_user.id] = {
        "type":"card",
        "level":call.data,
        "number":number
    }

    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="pay_crypto")]
    ])

    await msg.answer("Dooro Payment Method:", reply_markup=kb)
    await state.clear()

# ================= PAYMENT =================
@dp.callback_query(F.data == "pay_local")
async def pay_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(call: CallbackQuery):
    user = users[call.from_user.id]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])

    await bot.send_photo(
        ADMIN_ID,
        user["photo"],
        caption=(
            f"Card Request\n"
            f"Name: {user['name']}\n"
            f"Mother: {user['mother']}\n"
            f"Level: {user['level']}"
        ),
        reply_markup=kb
    )

    await call.message.edit_text("Codsiga waa la diray ⏳")

# ================= ADMIN =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    code = users[uid].get("code", generate_code())
    users[uid]["code"] = code

    await bot.send_message(
        uid,
        f"Approved ✅\nCode: {code}\n\nCodekan waxaa gelisaa CHECK CODE oo hel numberkaaga."
    )
    await call.message.edit_text("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "Rejected ❌")
    await call.message.edit_text("Rejected ❌")

# ================= CHECK CODE =================
@dp.message(F.text == "Check Code")
async def check_code(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-ka:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def verify(msg: Message, state: FSMContext):
    data = users.get(msg.from_user.id)
    if not data:
        await msg.answer("Wax order ah ma lihid ❌")
    elif msg.text == data.get("code"):
        await msg.answer(f"Number-kaaga:\n{data['number']}")
    else:
        await msg.answer("Code khaldan ❌")
    await state.clear()

# ================= CANCEL =================
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Cancelled ❌")

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
