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
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Haddii environment-ka uusan jirin, gali token si toos ah
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

class WithdrawState(StatesGroup):
    waiting_amount = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

def generate_referral_code():
    return "".join(str(random.randint(0, 9)) for _ in range(8))

async def live_animation(msg: Message, text="Checking", seconds=3):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START ==================
@dp.message(Command("start"))
async def start(msg: Message):
    uid = msg.from_user.id
    args = msg.get_args()

    # User cusub
    if uid not in users:
        referral_code = generate_referral_code()
        users[uid] = {
            "balance": 0.0,
            "referral_code": referral_code,
            "referrals": []
        }

    # Referral check
    if args:
        ref_code = args.strip()
        for user_id, data in users.items():
            if data["referral_code"] == ref_code and uid not in data["referrals"]:
                data["referrals"].append(uid)
                data["balance"] += 0.6
                await bot.send_message(user_id, f"🎉 Qof cusub ayaa ku soo biiray adiga! $0.6 ayaa lagu daray balance-kaaga.")
                break

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("New Order"), KeyboardButton("Customer")],
            [KeyboardButton("Balance"), KeyboardButton("Withdraw")]
        ],
        resize_keyboard=True
    )

    await msg.answer(
        f"Ku soo dhawoow Service Bot 🤖\nYour Referral Code: {users[uid]['referral_code']}\nBalance: ${users[uid]['balance']:.2f}",
        reply_markup=kb
    )

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)


# ================= CUSTOMER SUPPORT =================
@dp.message(F.text == "Customer")
async def customer_support(msg: Message):
    await msg.answer(
        "Customer Support 👇\n\n"
        "Fadlan la xiriir:\n"
        "@scholes1"
    )


# ================= BALANCE CHECK =================
@dp.message(F.text == "Balance")
async def balance(msg: Message):
    uid = msg.from_user.id
    bal = users.get(uid, {}).get("balance", 0.0)
    await msg.answer(f"💰 Balance-kaaga waa: ${bal:.2f}")


# ================= WITHDRAW REQUEST =================
@dp.message(F.text == "Withdraw")
async def withdraw(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    bal = users.get(uid, {}).get("balance", 0.0)

    if bal <= 0:
        await msg.answer("❌ Ma haysid balance ku filan oo aad ka bixi karto.")
        return

    await msg.answer(f"Fadlan geli lacagta aad rabto inaad ka baxsato. Balance-kaaga: ${bal:.2f}")
    await state.set_state(WithdrawState.waiting_amount)


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

    users[call.from_user.id]["current_order"] = {
        "type": "virtual",
        "platform": platform,
        "number": number,
        "price": 0.8
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_payment_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_payment_crypto")]
    ])

    await call.message.edit_text(
        f"Number: {number}\nQiimaha: $0.8\nDooro Payment:",
        reply_markup=kb
    )


# ================= CARD FLOW =================
@dp.callback_query(F.data == "card_start")
async def card_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LEVEL 1", callback_data="card_level_1")],
        [InlineKeyboardButton(text="LEVEL 2", callback_data="card_level_2")]
    ])
    await call.message.edit_text("Dooro Card Level:", reply_markup=kb)


@dp.callback_query(F.data.startswith("card_level_"))
async def card_level_selected(call: CallbackQuery):
    level = call.data.split("_")[-1]
    number = random_number()

    users[call.from_user.id]["current_order"] = {
        "type": "card",
        "card_type": f"LEVEL {level}",
        "number": number,
        "price": 5.0
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

# ================== LOCAL PAYMENT =================
@dp.callback_query(F.data == "v_payment_local")
async def virtual_local_payment(call: CallbackQuery):
    uid = call.from_user.id
    order = users[uid]["current_order"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n"
        f"Lambarkaaga: {order['number']}\nQiimaha: ${order['price']}",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def confirm_virtual_payment(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Fadlan soo dir screenshot-ka Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

@dp.message(StateFilter(VirtualState.waiting_screenshot), F.photo)
async def receive_virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    order = users[uid]["current_order"]
    users[uid]["current_order"]["screenshot"] = msg.photo[-1].file_id

    # U dir admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"),
            InlineKeyboardButton(text="SEND OTP", callback_data=f"admin_otp_{uid}")
        ]
    ])
    caption = (
        f"New Virtual Order\n"
        f"User: {uid}\n"
        f"Platform: {order['platform']}\n"
        f"Number: {order['number']}\n"
        f"Price: ${order['price']}"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await msg.answer("✅ Screenshot waa la soo diray, admin ayaa xaqiijin doona.")
    await state.clear()


# ================== CRYPTO PAYMENT =================
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto_payment(call: CallbackQuery):
    uid = call.from_user.id
    order = users[uid]["current_order"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_crypto_confirm_{uid}")]
    ])
    text = (
        f"💰 Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Lambarkaaga: {order['number']}\n"
        f"Qiimaha: ${order['price']}"
    )
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("v_crypto_confirm_"))
async def confirm_crypto(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Fadlan soo dir screenshot-ka Crypto Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)


# ================= ADMIN CONFIRM/REJECT =================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    order = users[uid]["current_order"]
    users[uid]["balance"] += order["price"]

    await bot.send_message(
        uid,
        f"✅ Payment Confirmed!\n"
        f"Number: {order['number']}\n"
        f"Platform/Level: {order.get('platform', order.get('card_type'))}\n"
        f"Price: ${order['price']}\n"
        f"Status: PAID ✅"
    )
    await call.message.edit_caption("✅ PAYMENT CONFIRMED")


@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta.")
    await call.message.edit_caption("❌ PAYMENT REJECTED")
    users[uid].pop("current_order", None)


# ================= ADMIN SEND OTP =================
@dp.callback_query(F.data.startswith("admin_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    otp = generate_otp()
    users[uid]["current_order"]["otp"] = otp
    users[uid]["current_order"]["otp_requests"] = 0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]
    ])
    await bot.send_message(uid,
        f"Number: {users[uid]['current_order']['number']}\n"
        f"Platform/Level: {users[uid]['current_order'].get('platform', users[uid]['current_order'].get('card_type'))}\n"
        f"PAYMENT: PAID ✅",
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
    uid = call.from_user.id

    users[uid]["current_order"] = {
        "type": "card",
        "card_type": f"LEVEL {level}",
        "number": number,
        "price": 5  # Fixed price
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_payment_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_payment_crypto")]
    ])

    await call.message.edit_text(
        f"Card Level: LEVEL {level}\n"
        f"Number: {number}\n"
        f"Price: $5\n\n"
        f"Dooro Payment:",
        reply_markup=kb
    )


# ================= CARD LOCAL PAYMENT =================
@dp.callback_query(F.data == "card_payment_local")
async def card_payment_local(call: CallbackQuery):
    uid = call.from_user.id
    order = users[uid]["current_order"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"card_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n\n"
        f"Number: {order['number']}\n"
        f"Level: {order['card_type']}\n"
        f"Price: ${order['price']}",
        reply_markup=kb
    )


# ================= CARD CRYPTO PAYMENT =================
@dp.callback_query(F.data == "card_payment_crypto")
async def card_payment_crypto(call: CallbackQuery):
    uid = call.from_user.id
    order = users[uid]["current_order"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"card_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Number: {order['number']}\n"
        f"Level: {order['card_type']}\n"
        f"Price: ${order['price']}",
        reply_markup=kb
    )


# ================= CARD CONFIRM =================
@dp.callback_query(F.data.startswith("card_confirm_payment_"))
async def card_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Fadlan soo dir screenshot-ka Payment-ka")
    await state.set_state(CardState.screenshot)


# ================= RECEIVE CARD SCREENSHOT =================
@dp.message(StateFilter(CardState.screenshot), F.photo)
async def receive_card_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    order = users[uid]["current_order"]
    users[uid]["current_order"]["screenshot"] = msg.photo[-1].file_id

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}"),
            InlineKeyboardButton(text="ASK", callback_data=f"admin_card_ask_{uid}")
        ]
    ])
    caption = (
        f"New CARD Order\n"
        f"User: {uid}\n"
        f"Level: {order['card_type']}\n"
        f"Number: {order['number']}\n"
        f"Price: ${order['price']}"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await msg.answer("✅ Screenshot waa la soo diray, admin ayaa xaqiijin doona.")
    await state.clear()


# ================= ADMIN CONFIRM CARD =================
@dp.callback_query(F.data.startswith("admin_card_confirm_"))
async def admin_card_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    order = users[uid]["current_order"]
    users[uid]["balance"] += order["price"]

    await bot.send_message(
        uid,
        f"✅ Payment Confirmed!\n"
        f"Number: {order['number']}\n"
        f"Level: {order['card_type']}\n"
        f"Price: ${order['price']}\n"
        f"Status: PAID ✅"
    )
    await call.message.edit_caption("✅ CARD PAYMENT CONFIRMED")


# ================= ADMIN REJECT CARD =================
@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta.")
    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")
    users[uid].pop("current_order", None)


# ================= ADMIN ASK CARD =================
@dp.callback_query(F.data.startswith("admin_card_ask_"))
async def admin_card_ask(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    await bot.send_message(uid, "ℹ️ Admin ayaa kula soo xiriiri doona si dalabka loo dhamaystiro.")
    await call.message.edit_caption("⚠️ ADMIN REQUESTED USER")

# ================= WITHDRAWAL =================
@dp.message(F.text == "Withdraw")
async def withdraw_request(msg: Message):
    uid = msg.from_user.id
    balance = users.get(uid, {}).get("balance", 0)

    if balance <= 0:
        await msg.answer("❌ Balance-kaaga waa eber, wax lacag ah ma bixi kartid.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM WITHDRAW", callback_data=f"withdraw_confirm_{uid}")]
    ])

    await msg.answer(f"💸 Balance-kaaga: ${balance:.2f}\nDo you want to withdraw?", reply_markup=kb)


# ================= CONFIRM WITHDRAWAL =================
@dp.callback_query(F.data.startswith("withdraw_confirm_"))
async def confirm_withdraw(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    balance = users.get(uid, {}).get("balance", 0)

    if balance <= 0:
        await call.message.edit_text("❌ Balance-kaaga waa eber, wax lacag ah ma bixi kartid.")
        return

    # U dir codsi admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"admin_withdraw_approve_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{uid}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"💰 User {uid} requested withdrawal: ${balance:.2f}",
        reply_markup=kb_admin
    )
    await call.message.edit_text("✅ Codsigaaga lacag bixinta waa la diray admin-ka. Sug xaqiijin.")


# ================= ADMIN APPROVE WITHDRAWAL =================
@dp.callback_query(F.data.startswith("admin_withdraw_approve_"))
async def admin_withdraw_approve(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    balance = users.get(uid, {}).get("balance", 0)

    if balance <= 0:
        await call.message.edit_text("❌ User balance already zero.")
        return

    users[uid]["balance"] = 0
    await bot.send_message(uid, f"✅ Withdrawal approved!\nLacag: ${balance:.2f} ayaa laguu diray.")
    await call.message.edit_text(f"✅ User {uid} withdrawal approved.")


# ================= ADMIN REJECT WITHDRAWAL =================
@dp.callback_query(F.data.startswith("admin_withdraw_reject_"))
async def admin_withdraw_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    await bot.send_message(uid, "❌ Codsigaaga withdrawal waa la diiday. Balance-kaaga wuu ahaanayaa sida uu yahay.")
    await call.message.edit_text(f"❌ User {uid} withdrawal rejected.")


# ================= REFERRAL SHOW =================
@dp.message(F.text == "My Referral")
async def my_referral(msg: Message):
    uid = msg.from_user.id
    data = users.get(uid, {})
    code = data.get("referral_code", "N/A")
    referrals = data.get("referrals", [])
    balance = data.get("balance", 0)

    await msg.answer(
        f"🎯 Referral Code: {code}\n"
        f"Referrals: {len(referrals)}\n"
        f"Balance: ${balance:.2f}"
    )


# ================= MAIN =================
async def main():
    logging.info("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
