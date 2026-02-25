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

# ✅ Aiogram 3.7+ compatible
bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}
pending_admin_register = {}
admin_request_timers = {}

# ================= STATES =================

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

# ================= HELPERS =================

def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

async def animation(message, text="Checking", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await message.edit_text(f"{text}{dots}")

# ================= START =================

@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ================= NEW ORDER =================

@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================== VIRTUAL SYSTEM ===================
# =====================================================

# -------- PLATFORM SELECTION --------
@dp.callback_query(F.data == "virtual_start")
async def virtual_platform(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="TIKTOK", callback_data="v_TIKTOK")],
        [InlineKeyboardButton(text="INSTAGRAM", callback_data="v_INSTAGRAM")],
        [InlineKeyboardButton(text="FACEBOOK", callback_data="v_FACEBOOK")],
        [InlineKeyboardButton(text="WHATSAPP", callback_data="v_WHATSAPP")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="v_TELEGRAM")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

# -------- PLATFORM CHOSEN --------
@dp.callback_query(F.data.startswith("v_"))
async def virtual_selected(call: CallbackQuery):
    platform = call.data.split("_")[1]
    number = random_number()

    users[call.from_user.id] = {
        "type": "virtual",
        "platform": platform,
        "number": number,
        "price": "$0.8"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])

    await call.message.edit_text(
        f"Number: {number}\n"
        f"Qiimaha: $0.8\n\n"
        f"Dooro Payment:",
        reply_markup=kb
    )

# -------- LOCAL PAYMENT --------
@dp.callback_query(F.data == "v_local")
async def virtual_local(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")]
    ])
    await call.message.edit_text(
        f"NUMBERKAN LACAGTA KU DIR\n"
        f"$0.8\n"
        f"{LOCAL_NUMBER}",
        reply_markup=kb
    )
    await state.set_state(VirtualState.waiting_screenshot)

# -------- CRYPTO PAYMENT --------
@dp.callback_query(F.data == "v_crypto")
async def virtual_crypto(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")]
    ])
    await call.message.edit_text(
        f"USDT:\n<code>{USDT_ADDRESS}</code>\n\n"
        f"BNB:\n<code>{BNB_ADDRESS}</code>",
        reply_markup=kb
    )
    await state.set_state(VirtualState.waiting_screenshot)

# -------- CONFIRM CLICKED --------
@dp.callback_query(F.data == "v_confirm")
async def virtual_confirm(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir PAYMENT (SCREENSHOT).")
    await state.set_state(VirtualState.waiting_screenshot)

# -------- RECEIVE SCREENSHOT (VIRTUAL) --------
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)

    if not data:
        await msg.answer("❌ Khalad: User data lama helin.")
        await state.clear()
        return

    # Save screenshot
    users[uid]["screenshot"] = msg.photo[-1].file_id

    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Inline keyboard for admin actions
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="REGISTER", callback_data=f"admin_register_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton(text="BAN", callback_data=f"admin_ban_{uid}")
        ]
    ])

    caption = (
        f"New Virtual Order\n\n"
        f"User: {uid}\n"
        f"Number: {data['number']}\n"
        f"Platform: {data['platform']}"
    )

    # Send screenshot to admin
    await bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    # 10 second timeout: if admin does nothing, prompt user
    async def timeout():
        await asyncio.sleep(10)
        if uid in users and not users[uid].get("otp_sent"):
            await bot.send_message(uid, "Fadlan soo Dalbo OTP.")

    asyncio.create_task(timeout())

    await state.clear()

# -------- ADMIN REJECT --------
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])

    await bot.send_message(uid, "❌ Payment lama xaqiijin.")
    await call.message.edit_caption("❌ Virtual Payment Rejected")

    users.pop(uid, None)

# -------- ADMIN BAN --------
@dp.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])

    await bot.send_message(uid, "⛔ Waxaa lagaa xanibay isticmaalka bot-kan.")
    await call.message.edit_caption("⛔ USER BANNED")

    users.pop(uid, None)

# -------- ADMIN REGISTER (ENTER OTP) --------
@dp.callback_query(F.data.startswith("admin_register_"))
async def admin_register_virtual(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[2])

    pending_admin_register[call.from_user.id] = uid

    await call.message.answer("Gali OTP aad rabto inaad siiso user-ka:")
    await state.set_state(AdminRegisterState.waiting_otp)

# -------- ADMIN SEND OTP TO USER --------
@dp.message(AdminRegisterState.waiting_otp)
async def admin_send_otp(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return  # Kaliya admin wuxuu gali karaa OTP

    if msg.from_user.id not in pending_admin_register:
        return

    uid = pending_admin_register[msg.from_user.id]
    otp = msg.text.strip()

    if not otp.isdigit():
        await msg.answer("❌ OTP waa inuu ahaadaa tiro.")
        return

    # Save OTP for user
    users[uid]["otp"] = otp
    users[uid]["otp_sent"] = True

    # User receives inline button to view OTP
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"OTP: {otp}", callback_data="show_otp")]
    ])

    await bot.send_message(
        uid,
        f"Number: {users[uid]['number']}\n"
        f"Platform: {users[uid]['platform']}\n\n"
        f"PAYMENT: PAID ✅",
        reply_markup=kb
    )

    await msg.answer("✅ OTP waa la diray.")
    await state.clear()
    pending_admin_register.pop(msg.from_user.id)

# -------- USER CLICK INLINE OTP --------
@dp.callback_query(F.data == "show_otp")
async def show_otp_animation(call: CallbackQuery):
    uid = call.from_user.id

    if uid not in users or "otp" not in users[uid]:
        await call.answer("❌ OTP lama helin.", show_alert=True)
        return

    otp = users[uid]["otp"]

    msg = await call.message.edit_text("OTP Loading...")
    await animation(msg, "OTP", 5)  # Live animation
    await call.message.edit_text(f"Your OTP Code:\n\n{otp}")


# -------- OTP INLINE CLICK (USER SIDE) --------

@dp.callback_query(F.data == "show_otp")
async def show_otp_animation(call: CallbackQuery):
    uid = call.from_user.id

    if uid not in users:
        return

    otp = users[uid].get("otp")

    msg = await call.message.edit_text("OTP Loading...")
    await animation(msg, "OTP", 5)

    await call.message.edit_text(f"Your OTP Code:\n\n{otp}")

# =====================================================
# ===================== CARD SYSTEM ===================
# =====================================================

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

    # haddii uusan sawir ahayn
    if not msg.photo:
        await msg.answer("❌ FADLAN SAWIRKAAGA SOO DIR (Face Only).")
        return

    face_id = msg.photo[-1].file_id
    await state.update_data(face=face_id)

    checking = await msg.answer("Checking...")
    await animation(checking, "Checking", 5)

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
        text = (
            f"NUMBERKAN LACAGTA KU DIR\n"
            f"{data['price']}\n"
            f"{LOCAL_NUMBER}"
        )
    else:
        text = (
            f"USDT:\n"
            f"<code>{USDT_ADDRESS}</code>\n\n"
            f"BNB:\n"
            f"<code>{BNB_ADDRESS}</code>"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment")]
    ])

    await call.message.edit_text(text, reply_markup=kb)


# -------- CONFIRM PAYMENT --------

@dp.callback_query(F.data == "card_confirm_payment")
async def card_confirm_payment(call: CallbackQuery, state: FSMContext):

    msg = await call.message.edit_text("Checking...")
    await animation(msg, "Checking", 5)

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

    await bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    await bot.send_photo(ADMIN_ID, data["face"])

    # 10 sec timeout haddii admin waxba qaban waayo
    async def timeout():
        await asyncio.sleep(10)
        await bot.send_message(uid, "Fadlan la xiriir admin si dalabka loo dhamaystiro.")

    asyncio.create_task(timeout())

    await state.clear()

# =====================================================
# =============== ADMIN CARD ACTIONS ==================
# =====================================================

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


# =====================================================
# ================= PROTECTION SYSTEM =================
# =====================================================

# Ka hortag fariimo random ah marka user-ku aanu ku jirin state
@dp.message()
async def ignore_unexpected(msg: Message, state: FSMContext):
    current_state = await state.get_state()

    # Haddii aanu jirin state shaqaynaya, iska indha tir
    if current_state is None:
        return


# =====================================================
# ================= CLEANUP SAFETY ====================
# =====================================================

async def safe_delete_user(uid: int):
    if uid in users:
        users.pop(uid, None)


# =====================================================
# ====================== MAIN =========================
# =====================================================

async def main():
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
