import os
import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command, StateFilter
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

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    screenshot = State()

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

def generate_referral_code():
    return "".join(str(random.randint(0, 9)) for _ in range(8))

async def return_to_main(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order")],
            [KeyboardButton(text="Customer")],
            [KeyboardButton(text="Balance")],
            [KeyboardButton(text="Referral")],
            [KeyboardButton(text="Withdrawal")],
            [KeyboardButton(text="Admin")],
        ],
        resize_keyboard=True
    )
    await msg.answer("Menu:", reply_markup=kb)

# ================= START COMMAND =================
@dp.message(Command("start"))
async def start(msg: Message):
    uid = msg.from_user.id
    if uid not in users:
        referral_code = generate_referral_code()
        users[uid] = {
            "balance": 0.0,
            "referral_code": referral_code,
            "referrals": []
        }

    args = msg.get_args()
    if args:
        ref_code = args.strip()
        for user_id, data in users.items():
            if data["referral_code"] == ref_code:
                if uid not in data["referrals"]:
                    data["referrals"].append(uid)
                    data["balance"] += 0.6
                    await bot.send_message(user_id, f"🎉 Qof cusub ayaa ku soo biiray adiga! $0.6 ayaa lagu daray balance-kaaga.")
                break

    await msg.answer(f"Ku soo dhawoow Service Bot 🤖\nYour Referral Code: {users[uid]['referral_code']}\nBalance: ${users[uid]['balance']:.2f}")
    await return_to_main(msg)

# ================= MENU OPTIONS =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

@dp.message(F.text == "Customer")
async def customer_support(msg: Message):
    await msg.answer("Customer Support 👇\n\nFadlan la xiriir:\n@scholes1")

@dp.message(F.text == "Balance")
async def show_balance(msg: Message):
    uid = msg.from_user.id
    balance = users.get(uid, {}).get("balance", 0.0)
    await msg.answer(f"💰 Your Balance: ${balance:.2f}")
    await return_to_main(msg)

@dp.message(F.text == "Referral")
async def show_referral(msg: Message):
    uid = msg.from_user.id
    code = users.get(uid, {}).get("referral_code", "N/A")
    referrals = users.get(uid, {}).get("referrals", [])
    await msg.answer(f"🔗 Your Referral Code: {code}\n👥 Referrals Count: {len(referrals)}")
    await return_to_main(msg)

@dp.message(F.text == "Withdrawal")
async def withdrawal(msg: Message):
    uid = msg.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="withdraw_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="withdraw_crypto")]
    ])
    await msg.answer("Choose Withdrawal Method:", reply_markup=kb)

@dp.message(F.text == "Admin")
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Add Balance", callback_data="admin_add_balance")]
    ])
    await msg.answer("⚙️ Admin Panel:", reply_markup=kb)

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
        f"Number: {number}\nQiimaha: $0.8\nDooro Payment:",
        reply_markup=kb
    )

# ================= VIRTUAL LOCAL PAYMENT =================
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local_payment(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n"
        f"Lambarkaaga: {data['number']}\nQiimaha: {data['price']}",
        reply_markup=kb
    )

# ================= VIRTUAL CRYPTO PAYMENT =================
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto_payment(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_crypto_confirm_{uid}")]
    ])

    text = (
        f"💰 Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Lambarkaaga: {data['number']}\n"
        f"Qiimaha: {data['price']}"
    )

    await call.message.edit_text(text, reply_markup=kb)

# ================= CONFIRM PAYMENTS =================
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def confirm_virtual_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg)
    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

@dp.callback_query(F.data.startswith("v_crypto_confirm_"))
async def confirm_crypto_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Crypto Payment...")
    await live_animation(msg)
    await call.message.answer("Soo dir Screenshot-ka Crypto Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

# ================= RECEIVE VIRTUAL SCREENSHOT =================
@dp.message(StateFilter(VirtualState.waiting_screenshot), F.photo)
async def receive_virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

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
        f"Payment: LOCAL/CRYPTO"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await state.clear()

# ================= ADMIN CONFIRM/REJECT =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, f"✅ Payment Confirmed\nNumber: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\nStatus: PAID ✅")
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users.pop(uid, None)

# ================= ADMIN SEND OTP =================
@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])

    await bot.send_message(
        uid,
        f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\nPAYMENT: PAID ✅",
        reply_markup=kb
    )

    await call.message.edit_caption("OTP sent to user")

# ================= CARD START =================
@dp.callback_query(F.data == "card_start")
async def card_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LEVEL 1", callback_data="card_level_1")],
        [InlineKeyboardButton(text="LEVEL 2", callback_data="card_level_2")]
    ])
    await call.message.edit_text("Dooro Card Level:", reply_markup=kb)

# ================= SELECT CARD LEVEL =================
@dp.callback_query(F.data.startswith("card_level_"))
async def card_level_selected(call: CallbackQuery):
    level = call.data.split("_")[-1]
    number = random_number()

    users[call.from_user.id] = {
        "type": "card",
        "card_type": f"LEVEL {level}",
        "number": number,
        "price": "$5"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_payment_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_payment_crypto")]
    ])

    await call.message.edit_text(
        f"Card Level: LEVEL {level}\n"
        f"Number: {number}\n"
        f"Qiimaha: $5\n\n"
        f"Dooro Payment:",
        reply_markup=kb
    )

# ================= CARD LOCAL PAYMENT =================
@dp.callback_query(F.data == "card_payment_local")
async def card_payment_local(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"card_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n\n"
        f"Number: {data['number']}\n"
        f"Level: {data['card_type']}\n"
        f"Qiimaha: {data['price']}",
        reply_markup=kb
    )

# ================= CARD CRYPTO PAYMENT =================
@dp.callback_query(F.data == "card_payment_crypto")
async def card_payment_crypto(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"card_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Number: {data['number']}\n"
        f"Level: {data['card_type']}\n"
        f"Qiimaha: {data['price']}",
        reply_markup=kb
    )

# ================= CARD CONFIRM =================
@dp.callback_query(F.data.startswith("card_confirm_payment_"))
async def card_confirm(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment...")
    await live_animation(msg)
    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(CardState.screenshot)

# ================= RECEIVE CARD SCREENSHOT =================
@dp.message(StateFilter(CardState.screenshot), F.photo)
async def receive_card_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid)

    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.")

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}"),
            InlineKeyboardButton(text="ASK", callback_data=f"admin_card_ask_{uid}")
        ]
    ])

    caption = (
        f"New CARD Order\n\n"
        f"User: {uid}\n"
        f"Level: {data['card_type']}\n"
        f"Number: {data['number']}\n"
        f"Price: {data['price']}"
    )

    await bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=caption,
        reply_markup=kb_admin
    )

    await state.clear()

# ================= ADMIN CONFIRM/REJECT/ASK CARD =================
@dp.callback_query(F.data.startswith("admin_card_confirm_"))
async def admin_card_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    data = users.get(uid)
    await bot.send_message(
        uid,
        f"✅ Payment Confirmed!\n\n"
        f"Number: {data['number']}\n"
        f"Level: {data['card_type']}\n"
        f"Status: PAID ✅"
    )
    await call.message.edit_caption("✅ CARD PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta.")
    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")
    users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_card_ask_"))
async def admin_card_ask(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    await bot.send_message(uid, "ℹ️ Admin ayaa kula soo xiriiri doona si dalabka loo dhamaystiro.")
    await call.message.edit_caption("⚠️ ADMIN REQUESTED USER")

# ================= MAIN =================
async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
