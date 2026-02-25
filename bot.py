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

# ================== VIRTUAL LOCAL PAYMENT FULL FLOW ===================

# 1️⃣ User clicks LOCAL
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if uid not in users:
        await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        return

    number = users[uid]["number"]
    price = users[uid]["price"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Fadlan lacagta ku dir lambarkan:\n\n{LOCAL_NUMBER}\nLambarkaaga: {number}\nQiimaha: {price}",
        reply_markup=kb
    )

# 2️⃣ User clicks CONFIRM → Checking animation → request screenshot
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def virtual_confirm_payment(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[-1])
    msg = await call.message.edit_text("Checking...")
    for i in range(5):
        await asyncio.sleep(1)
        await msg.edit_text(f"Checking{'.'* (i%4)}")

    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (PAYMENT)")
    await state.set_state(VirtualState.waiting_screenshot)

# 3️⃣ User sends screenshot → Admin receives screenshot + inline buttons
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id

    kb_admin = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton(text="OTP", callback_data=f"admin_otp_{uid}")
        ]
    ])

    caption = (
        f"New Virtual Order\n"
        f"User: {uid}\n"
        f"Platform: {data['platform']}\n"
        f"Number: {data['number']}\n"
        f"Payment Type: LOCAL"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")
    await state.clear()

# 4️⃣ Admin CONFIRM → notify user
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

# 5️⃣ Admin REJECT → notify user
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacagta dib u soo dir.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

# 6️⃣ Admin OTP → hidden OTP → user inline SHOW OTP
@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0  # track OTP check count

    kb_user = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])

    await bot.send_message(
        uid,
        f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅",
        reply_markup=kb_user
    )

    await call.message.edit_caption("OTP sent to user (hidden from admin)")

# 7️⃣ User clicks SHOW OTP → animation → OTP displayed
@dp.callback_query(F.data == "show_otp_user")
async def show_otp_user(call: CallbackQuery):
    uid = call.from_user.id
    otp = users[uid].get("otp")
    if not otp:
        await call.message.edit_text("❌ OTP lama helin, fadlan la xiriir admin.")
        return

    msg = await call.message.edit_text("OTP Loading...")
    for i in range(5):
        await asyncio.sleep(1)
        await msg.edit_text(f"OTP{'.'* (i%4)}")

    kb_check = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb_check)

# 8️⃣ User clicks CHECK AGAIN → generate new OTP + animation + admin notification after 2 attempts
@dp.callback_query(F.data == "check_again_otp")
async def check_again_otp(call: CallbackQuery):
    uid = call.from_user.id
    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp

    msg = await call.message.edit_text("Generating new OTP...")
    for i in range(5):
        await asyncio.sleep(1)
        await msg.edit_text(f"OTP{'.'* (i%4)}")

    kb_check = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb_check)

    # Notify admin after 2 attempts
    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="CONFIRM OTP", callback_data=f"admin_final_confirm_{uid}")]
        ])
        await bot.send_message(ADMIN_ID, f"User {uid} has requested OTP 2 times. Confirm final OTP.", reply_markup=kb_admin)

# 9️⃣ Admin final confirm OTP → notify user
@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")
    await bot.send_message(uid, f"✅ OTP Final Confirmed: {final_otp}\nYour payment is now fully verified!")
    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

# ================= VIRTUAL CRYPTO PAYMENT =================
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto(call: CallbackQuery):
    uid = call.from_user.id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm_crypto")]])
    await call.message.edit_text(
        f"USDT:\n<code>{USDT_ADDRESS}</code>\nBNB:\n<code>{BNB_ADDRESS}</code>",
        reply_markup=kb
    )

@dp.callback_query(F.data == "v_confirm_crypto")
async def virtual_confirm_crypto(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir SCREENSHOT-ka lacag bixinta (PAYMENT).")
    await state.set_state(VirtualState.waiting_screenshot)

# ===== RECEIVE SCREENSHOT (Virtual Local & Crypto) =====
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Admin Inline Keyboard
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton(text="OTP", callback_data=f"admin_otp_{uid}")
        ]
    ])
    caption = f"New Virtual Order\nUser: {uid}\nPlatform: {data['platform']}\nNumber: {data['number']}\nPayment Type: {data['type'].upper()}"
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await state.clear()

# ================= ADMIN ACTIONS (Virtual) =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacag dib u soo dir.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]])
    await bot.send_message(uid,
        f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅",
        reply_markup=kb
    )
    await call.message.edit_caption("OTP sent to user (hidden from admin)")

# ================= USER VIEW OTP =================
@dp.callback_query(F.data == "show_otp_user")
async def show_otp_user(call: CallbackQuery):
    uid = call.from_user.id
    otp = users[uid].get("otp")
    if not otp:
        await call.message.edit_text("❌ OTP lama helin, fadlan la xiriir admin.")
        return
    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP", 5)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]])
    await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb)

@dp.callback_query(F.data == "check_again_otp")
async def check_again_otp(call: CallbackQuery):
    uid = call.from_user.id
    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp
    msg = await call.message.edit_text("Generating new OTP...")
    await live_animation(msg, "OTP", 5)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]])
    await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb)

    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM OTP", callback_data=f"admin_final_confirm_{uid}")]])
        await bot.send_message(ADMIN_ID, f"User {uid} has requested OTP 2 times. Confirm final OTP.", reply_markup=kb_admin)

@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")
    await bot.send_message(uid, f"✅ OTP Final Confirmed: {final_otp}\nYour payment is now fully verified!")
    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

# ===================== CARD SYSTEM ===================

# -------- CARD START --------
@dp.callback_query(F.data == "card_start")
async def card_start(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="NORMAL ($1)", callback_data="card_type_normal")],
        [InlineKeyboardButton(text="VIP ($2)", callback_data="card_type_vip")]
    ])
    await call.message.edit_text("Dooro Nooca Card:", reply_markup=kb)

# -------- CARD TYPE SELECTED --------
@dp.callback_query(F.data.startswith("card_type_"))
async def card_type_selected(call: CallbackQuery, state: FSMContext):
    if call.data == "card_type_normal":
        price = "$1"
        ctype = "NORMAL"
    else:
        price = "$2"
        ctype = "VIP"

    await state.update_data(price=price, card_type=ctype)
    await call.message.answer("Geli Magacaaga Saddex Magac (Tusaale: Ahmed Ali Jama):")
    await state.set_state(CardState.fullname)

# -------- FULL NAME VALIDATION --------
@dp.message(CardState.fullname)
async def card_fullname(msg: Message, state: FSMContext):
    parts = msg.text.strip().split()
    if len(parts) != 3 or not all(p.isalpha() for p in parts):
        await msg.answer("❌ Fadlan geli 3 magac sax ah (Tusaale: Ahmed Ali Jama)")
        return
    await state.update_data(fullname=msg.text.strip())
    await msg.answer("Geli Magaca Hooyada (Hal Magac oo xarfo kaliya ah):")
    await state.set_state(CardState.mother)

# -------- MOTHER NAME VALIDATION --------
@dp.message(CardState.mother)
async def card_mother(msg: Message, state: FSMContext):
    if not msg.text.isalpha():
        await msg.answer("❌ Magaca hooyada waa inuu ahaadaa xarfo kaliya.")
        return
    await state.update_data(mother=msg.text.strip())
    await msg.answer("Fadlan soo dir Sawirkaaga (Face Only).")
    await state.set_state(CardState.face)

# -------- FACE ONLY CHECK --------
@dp.message(CardState.face)
async def card_face_validation(msg: Message, state: FSMContext):
    if not msg.photo:
        await msg.answer("❌ FADLAN SAWIRKAAGA SOO DIR (Face Only).")
        return
    face_id = msg.photo[-1].file_id
    await state.update_data(face=face_id)

    checking = await msg.answer("Checking...")
    await live_animation(checking, "Checking", 5)

    number = random_number()
    data = await state.get_data()
    await state.update_data(number=number)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_pay_crypto")]
    ])

    await msg.answer(
        f"Number: {number}\n"
        f"Qiimaha: {data['price']}\n\n"
        f"Dooro Payment Method:",
        reply_markup=kb
    )
    await state.set_state(CardState.payment_method)

# -------- PAYMENT METHOD --------
@dp.callback_query(F.data.startswith("card_pay_"))
async def card_payment_method(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if call.data == "card_pay_local":
        text = f"NUMBERKAN LACAGTA KU DIR\n{data['price']}\n{LOCAL_NUMBER}"
    else:
        text = f"USDT:\n<code>{USDT_ADDRESS}</code>\n\nBNB:\n<code>{BNB_ADDRESS}</code>"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# -------- CONFIRM PAYMENT --------
@dp.callback_query(F.data == "card_confirm_payment")
async def card_confirm_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka Lacag Bixinta.")
    await state.set_state(CardState.screenshot)

# -------- RECEIVE SCREENSHOT --------
@dp.message(CardState.screenshot, F.photo)
async def card_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = await state.get_data()
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}")
        ]
    ])

    caption = (
        f"New CARD Order\n\n"
        f"User: {uid}\n"
        f"Type: {data['card_type']}\n"
        f"Full Name: {data['fullname']}\n"
        f"Mother: {data['mother']}\n"
        f"Number: {data['number']}\n"
        f"Price: {data['price']}"
    )

    # Send screenshot + face to admin
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await bot.send_photo(ADMIN_ID, data["face"])

    # Timeout if admin does nothing
    async def timeout():
        await asyncio.sleep(10)
        await bot.send_message(uid, "Fadlan la xiriir admin si dalabka loo dhamaystiro.")
    asyncio.create_task(timeout())

    await state.clear()

# -------- ADMIN CONFIRM/REJECT --------
@dp.callback_query(F.data.startswith("admin_card_confirm_"))
async def admin_card_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    await bot.send_message(uid, "✅ Dalabkaaga waa la Ansixiyay.")
    await call.message.edit_caption("✅ CARD PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    await bot.send_message(uid, "❌ Payment lama xaqiijin.")
    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")

# ================= PROTECTION SYSTEM =================
# Ka hortag fariimo random ah marka user-ku aanu ku jirin state
@dp.message()
async def ignore_unexpected(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    # Haddii aanu jirin state shaqaynaya, iska indha tir
    if current_state is None:
        return

# ================= CLEANUP SAFETY =================
async def safe_delete_user(uid: int):
    if uid in users:
        users.pop(uid, None)

# ================= LOGGING SAFETY =================
logging.getLogger("aiogram").setLevel(logging.INFO)

# ================= MAIN =================
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
