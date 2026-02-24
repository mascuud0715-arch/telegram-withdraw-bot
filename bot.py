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

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654
LOCAL_NUMBER = "+252907868526"

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ========== STATES ==========
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    face_photo = State()
    payment_screenshot = State()

class VirtualState(StatesGroup):
    payment_screenshot = State()

class AskState(StatesGroup):
    message = State()

class CodeState(StatesGroup):
    code = State()

# ========== HELPERS ==========
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4, 9))
    return "+25263" + d*3 + str(random.randint(0, 9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="pay_crypto")]
    ])

# ========== START ==========
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("New Order"), KeyboardButton("Check Code")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ========== NEW ORDER ==========
@dp.message(F.text=="New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIRTUAL ($0.8)", callback_data="virtual")],
        [InlineKeyboardButton("CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ========== VIRTUAL ==========
@dp.callback_query(F.data=="virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton("TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton("Google", callback_data="v_Google")],
        [InlineKeyboardButton("Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_platform(call: CallbackQuery):
    uid = call.from_user.id
    number = normal_number()
    users[uid] = {
        "type":"virtual",
        "platform":call.data.replace("v_",""),
        "number":number,
        "amount":"$0.8",
        "crypto_pending": False,
        "code": None
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("LOCAL", callback_data="v_pay_local")],
        [InlineKeyboardButton("CRYPTO", callback_data="v_pay_crypto")]
    ])
    await call.message.edit_text(
        f"Platform: {users[uid]['platform']}\n"
        f"Number: {number}\n"
        f"Qiimaha: $0.8\n"
        "Dooro Payment Method:", reply_markup=kb
    )

# ========== CARD ==========
@dp.callback_query(F.data=="card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("VIP - $15", callback_data="vip")],
        [InlineKeyboardButton("NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip","normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    number = vip_number() if call.data=="vip" else normal_number()
    users[uid] = {
        "type":"card",
        "level":call.data,
        "number":number,
        "amount":"$15" if call.data=="vip" else "$1"
    }
    await call.message.answer("Fadlan geli Magacaaga Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    if len(msg.text.split()) <3:
        await msg.answer("Magac sax ah geli (3 magac)")
        return
    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirka Wajigaaga (Face photo):")
    await state.set_state(CardState.face_photo)

    # ===================== PAYMENT SCREENSHOT TO ADMIN =====================
@dp.message(CardState.payment_screenshot, F.photo)
async def payment_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Payment Screenshot waa la helay ⏳ Sug ansixinta Admin.")
    await state.clear()

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("CONFIRM", callback_data=f"admin_confirm_{uid}")],
        [InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{uid}")],
        [InlineKeyboardButton("ASK", callback_data=f"admin_ask_{uid}")]
    ])

    await bot.send_photo(
        ADMIN_ID,
        users[uid].get("face_photo", users[uid].get("photo")),
        caption=(
            f"New Request\n"
            f"User: {uid}\n"
            f"Type: {users[uid]['type']}\n"
            f"Platform: {users[uid].get('platform','N/A')}\n"
            f"Level: {users[uid].get('level','N/A')}\n"
            f"Number: {users[uid]['number']}\n"
            f"Name: {users[uid].get('name','N/A')}\n"
            f"Mother: {users[uid].get('mother','N/A')}\n"
            f"Amount: {users[uid]['amount']}"
        ),
        reply_markup=kb_admin
    )

    await bot.send_photo(
        ADMIN_ID,
        users[uid]["screenshot"],
        caption="Payment Screenshot"
    )

# ===================== ADMIN ACTIONS =====================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid not in users:
        await call.answer("User not found")
        return

    code = generate_code()
    users[uid]["code"] = code

    # Card user → CHECK CODE
    if users[uid]["type"]=="card":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("CHECK CODE", callback_data="go_check")]])
        await bot.send_message(uid, f"Payment Confirmed ✅\nCode-kaaga ku qor CHECK CODE:\n\n{code}", reply_markup=kb)
    # Virtual → OTP
    elif users[uid]["type"]=="virtual":
        otp_msg = await bot.send_message(uid, f"OTP Ready ✅\nNumber: {users[uid]['number']}\nCode: {code}")
        # OTP animation
        for step in ["OTP Generating.", "OTP Generating..", "OTP Generating...", "OTP Ready!"]:
            await asyncio.sleep(1)
            await otp_msg.edit_text(f"{step}\nNumber: {users[uid]['number']}\nCode: {code}")

    await call.message.edit_text("Approved ✅")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid in users:
        await bot.send_message(uid,
            f"❌ Codsigaaga waa la diiday\n"
            f"Fadlan lacagta ku dir Number-kan si loo xaqiijiyo: {LOCAL_NUMBER}")
    await call.message.edit_text("Rejected ❌")

@dp.callback_query(F.data.startswith("admin_ask_"))
async def admin_ask(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[2])
    await call.message.answer("Fariin qor user-ka:")
    await state.update_data(ask_user_id=uid)
    await state.set_state(AskState.message)

@dp.message(AskState.message)
async def send_ask(msg: Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("ask_user_id")
    if uid:
        await bot.send_message(uid, f"Message from Admin:\n{msg.text}")
        await msg.answer("Fariinta waa la diray ✅")
    await state.clear()

# ===================== CHECK CODE =====================
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

    if uid in users and users[uid].get("type") in ["card","virtual"]:
        if users[uid].get("code")==code_input:
            await msg.answer(f"✅ Code Confirmed\nNumber-kaaga waa:\n{users[uid]['number']}")
        else:
            # Khalad: dib u tus Number + Payment options
            await msg.answer(
                f"❌ Code Khaldan\nNumber: {users[uid]['number']}\nQiimaha: {users[uid]['amount']}\nDooro Payment Method:",
                reply_markup=payment_keyboard()
            )
    else:
        await msg.answer("Ma jiro dalab la helay.")

    await state.clear()

# ===================== FORWARD CARD INFO =====================
@dp.message()
async def forward_card(msg: Message):
    uid = msg.from_user.id
    if uid in users and users[uid].get("type")=="card" and "screenshot" in users[uid]:
        data = users[uid]
        kb_admin = InlineKeyboardMarkup([
            [InlineKeyboardButton("CONFIRM", callback_data=f"admin_confirm_{uid}")],
            [InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{uid}")],
            [InlineKeyboardButton("ASK", callback_data=f"admin_ask_{uid}")]
        ])
        await bot.send_photo(ADMIN_ID, data["face_photo"], caption=(
            f"Card Request\nUser:{uid}\nLevel:{data['level']}\nNumber:{data['number']}\nName:{data['name']}\nMother:{data['mother']}"
        ), reply_markup=kb_admin)
        await bot.send_photo(ADMIN_ID, data["screenshot"], caption="Payment Screenshot")

# ===================== MAIN POLLING =====================
async def main():
    logging.info("Bot-ka waa bilaabmay...")
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
