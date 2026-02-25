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
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# User Data & Admin Tracking
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

# -------- PLATFORM SELECTION --------
@dp.callback_query(F.data == "virtual_start")
async def virtual_platform(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="v_platform_WHATSAPP")],
        [InlineKeyboardButton(text="INSTAGRAM", callback_data="v_platform_INSTAGRAM")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="v_platform_TELEGRAM")],
        [InlineKeyboardButton(text="GOOGLE", callback_data="v_platform_GOOGLE")],
        [InlineKeyboardButton(text="TIKTOK", callback_data="v_platform_TIKTOK")],
        [InlineKeyboardButton(text="FACEBOOK", callback_data="v_platform_FACEBOOK")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)


# -------- PLATFORM SELECTED --------
@dp.callback_query(F.data.startswith("v_platform_"))
async def virtual_platform_selected(call: CallbackQuery):
    platform = call.data.split("_")[2]
    number = random_number()

    users[call.from_user.id] = {
        "type": "virtual",
        "platform": platform,
        "number": number,
        "price": "$0.8"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_payment_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_payment_crypto")]
    ])
    await call.message.edit_text(
        f"Number: {number}\nQiimaha: $0.8\nDooro Payment:",
        reply_markup=kb
    )

# ======= VIRTUAL LOCAL PAYMENT FULL =======
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if uid not in users:
        return await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")

    number = users[uid]["number"]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("CONFIRM", callback_data=f"v_confirm_payment_{uid}")]])
    await call.message.edit_text(f"Fadlan lacagta ku dir lambarkan:\n\n{LOCAL_NUMBER}\nLambarkaaga: {number}", reply_markup=kb)

# CONFIRM clicked → animation → ask for screenshot
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def virtual_confirm_payment(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[-1])
    msg = await call.message.edit_text("Checking payment...")
    await live_animation(msg, "Checking", 5)  # Live animation
    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (PAYMENT)")
    await state.set_state(VirtualState.waiting_screenshot)

# Receive screenshot from user → send to admin with inline buttons
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if uid not in users:
        await msg.answer("❌ Dalabka lama helin.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Inline buttons for admin: CONFIRM / REJECT / OTP
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("CONFIRM", callback_data=f"admin_confirm_{uid}"),
            InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton("OTP", callback_data=f"admin_otp_{uid}")
        ]
    ])

    caption = (
        f"New Virtual Order (LOCAL)\n"
        f"User: {uid}\n"
        f"Platform: {users[uid]['platform']}\n"
        f"Number: {users[uid]['number']}"
    )

    # Send screenshot to admin
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await state.clear()

# Admin CONFIRM → notify user
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    msg = await call.message.edit_caption("✅ PAYMENT CONFIRMED")
    await live_animation(msg, "Notifying user...", 3)
    await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.")

# Admin REJECT → notify user
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    msg = await call.message.edit_caption("❌ PAYMENT REJECTED")
    await live_animation(msg, "Notifying user...", 3)
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacagta dib u soo dir.")
    users.pop(uid, None)

# Admin OTP → hidden OTP → user inline SHOW OTP
@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("SHOW OTP", callback_data="show_otp_user")]])
    await bot.send_message(uid, f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅", reply_markup=kb)
    await call.message.edit_caption("OTP sent to user (hidden from admin)")

# ================== VIRTUAL CRYPTO PAYMENT ===================

@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto_payment(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if uid not in users:
        await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_crypto_{uid}")]
    ])
    await call.message.edit_text(
        f"USDT:\n<code>{USDT_ADDRESS}</code>\nBNB:\n<code>{BNB_ADDRESS}</code>",
        reply_markup=kb
    )

# -------- CONFIRM CLICKED (CRYPTO) --------
@dp.callback_query(F.data.startswith("v_confirm_crypto_"))
async def virtual_confirm_crypto(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[-1])
    msg = await call.message.edit_text("Checking Crypto Payment...")
    await animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (CRYPTO).")
    await state.set_state(VirtualState.waiting_screenshot)

# ================== VIRTUAL RECEIVE SCREENSHOT ===================
@dp.message(VirtualState.waiting_screenshot, F.photo)
async def virtual_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup([
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
        f"Payment Type: {'LOCAL' if 'v_confirm_payment' in msg.text else 'CRYPTO'}"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")
    await state.clear()

# ================== ADMIN CONFIRM / REJECT / OTP ===================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacagta dib u soo dir.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp_virtual(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])
    await bot.send_message(
        uid,
        f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅",
        reply_markup=kb
    )
    await call.message.edit_caption("OTP sent to user (hidden from admin)")

# -------- SHOW OTP USER INLINE --------
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
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb)

# -------- CHECK AGAIN OTP --------
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
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb)

    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="CONFIRM OTP", callback_data=f"admin_final_confirm_{uid}")]
        ])
        await bot.send_message(ADMIN_ID, f"User {uid} requested OTP 2 times. Confirm final OTP.", reply_markup=kb_admin)

# -------- ADMIN FINAL CONFIRM OTP --------
@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")
    await bot.send_message(uid, f"✅ OTP Final Confirmed: {final_otp}\nYour payment is now fully verified!")
    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

# ===================== CARD PAYMENT SYSTEM =====================

# -------- CARD LOCAL PAYMENT --------
@dp.callback_query(F.data == "card_pay_local")
async def card_local_payment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uid = call.from_user.id
    text = f"Fadlan lacagta ku dir lambarkan:\n{LOCAL_NUMBER}\nQiimaha: {data['price']}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment_local")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# -------- CARD CRYPTO PAYMENT --------
@dp.callback_query(F.data == "card_pay_crypto")
async def card_crypto_payment(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment_crypto")]
    ])
    await call.message.edit_text(
        f"USDT:\n<code>{USDT_ADDRESS}</code>\nBNB:\n<code>{BNB_ADDRESS}</code>",
        reply_markup=kb
    )

# -------- CONFIRM PAYMENT (LOCAL/CRYPTO) --------
@dp.callback_query(F.data.startswith("card_confirm_payment_"))
async def card_confirm_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment...")
    await animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (CARD).")
    await state.set_state(CardState.screenshot)

# -------- RECEIVE SCREENSHOT --------
@dp.message(CardState.screenshot, F.photo)
async def card_receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = await state.get_data()
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Inline keyboard for admin
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}")
        ]
    ])

    caption = (
        f"New CARD Order\n"
        f"User: {uid}\n"
        f"Type: {data['card_type']}\n"
        f"Full Name: {data['fullname']}\n"
        f"Mother: {data['mother']}\n"
        f"Number: {data['number']}\n"
        f"Price: {data['price']}"
    )

    # Send screenshot to admin
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb)
    await bot.send_photo(ADMIN_ID, data["face"])

    # 10 sec timeout to prompt user if admin doesn't respond
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

# ===================== PROTECTION & TIMEOUT SYSTEM =====================

# Live animation helper
async def live_animation(message: Message, text="Loading", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await message.edit_text(f"{text}{dots}")

# ================= USER STATE PROTECTION =================
@dp.message()
async def ignore_unexpected(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    # Haddii user aanu ku jirin state shaqaynaya, iska indha tir
    if current_state is None:
        return

# ================= VIRTUAL PAYMENT TIMEOUT =================
async def virtual_admin_timeout(uid: int):
    await asyncio.sleep(10)
    if uid in users and not users[uid].get("otp_sent"):
        await bot.send_message(uid, "⚠️ Fadlan soo Dalbo OTP si dalabka loo dhameystiro.")

# ================= CARD PAYMENT TIMEOUT =================
async def card_admin_timeout(uid: int):
    await asyncio.sleep(10)
    await bot.send_message(uid, "⚠️ Fadlan la xiriir admin si dalabka loo dhamaystiro.")

# ================= CLEANUP USERS =================
async def safe_delete_user(uid: int):
    if uid in users:
        users.pop(uid, None)

# ================= LOGGING SAFETY =================
logging.getLogger("aiogram").setLevel(logging.INFO)

# ================= GLOBAL ERROR HANDLER =================
@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Update: {update} raised exception {exception}")

# ================= RUN BOT =================
async def main():
    print("Bot running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
