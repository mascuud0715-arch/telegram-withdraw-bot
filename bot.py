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

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

LOCAL_NUMBER = "+252907868526"
BNB_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
USDT_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

# Bot initialization with HTML parse mode (DefaultBotProperties removed)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= DATA STORAGE =================
users = {}
withdraw_requests = {}  # key = request_id
REQUEST_ID = 29012

stats = {
    "total_users": 0,
    "total_virtual": 0,
    "total_card": 0
}

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    screenshot = State()

class WithdrawState(StatesGroup):
    waiting_local = State()
    waiting_crypto = State()

class AdminAddBalanceState(StatesGroup):
    waiting_data = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp():
    return "".join(random.choices("0123456789", k=6))

def generate_referral():
    return "".join(random.choices("0123456789", k=10))

async def live_animation(msg: Message, text="Checking", seconds=5):
    for i in range(seconds):
        dots = "." * (i % 4)
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}{dots}")

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    uid = msg.from_user.id

    # Haddii user cusub yahay, ku dar dict-ka
    if uid not in users:
        users[uid] = {
            "balance": 0.0,
            "referrals": [],
            "ref_code": generate_referral(),
            "type": None,
            "number": None,
            "platform": None,
            "card_type": None,
            "price": 0,
            "otp": None,
            "otp_requests": 0,
            "screenshot": None
        }
        stats["total_users"] += 1

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
            [KeyboardButton(text="Withdrawal")]
        ],
        resize_keyboard=True
    )

    # Admin panel button, kaliya admin arko
    if uid == ADMIN_ID:
        kb.add(KeyboardButton(text="Admin Panel"))

    await msg.answer(
        "Ku soo dhawoow Service Bot 🤖\nDooro waxa aad rabto:",
        reply_markup=kb
    )

# ================= BALANCE =================
@dp.message(F.text == "Balance")
async def show_balance(msg: Message):
    uid = msg.from_user.id
    user = users.get(uid)
    if not user:
        await msg.answer("❌ User lama helin.")
        return

    await msg.answer(f"💰 Balance-kaaga hadda: ${user['balance']:.2f}")

# ================= REFERRAL =================
@dp.message(F.text == "Referral")
async def show_referral(msg: Message):
    uid = msg.from_user.id
    user = users.get(uid)
    if not user:
        await msg.answer("❌ User lama helin.")
        return

    ref_list = user.get("referrals", [])
    text = f"👥 Referral Code: {user['ref_code']}\n"
    text += f"Number of referrals: {len(ref_list)}\n"
    text += "\nReferred Users:\n"
    for r in ref_list:
        text += f"- {r}\n"
    await msg.answer(text)

# ================= WITHDRAWAL =================
@dp.message(F.text == "Withdrawal")
async def withdrawal_menu(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="LOCAL"), KeyboardButton(text="CRYPTO")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await msg.answer("💸 Dooro habka lacag bixinta:", reply_markup=kb)

# ================= ADMIN PANEL =================
@dp.message(F.text == "Admin Panel")
async def admin_panel(msg: Message):
    uid = msg.from_user.id
    if uid != ADMIN_ID:
        await msg.answer("❌ Kaliya admin ayaa arki kara panel-kan.")
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
    await msg.answer("⚙️ Admin Panel:", reply_markup=kb)

# ================= WITHDRAWAL LOCAL =================
@dp.message(F.text == "LOCAL")
async def withdrawal_local(msg: Message):
    uid = msg.from_user.id
    user = users.get(uid)
    if not user:
        await msg.answer("❌ User lama helin.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Back")]],
        resize_keyboard=True
    )

    await msg.answer(
        f"🤑 Fadlan soo dir Number-kaaga si lacagta lagugu diro (Min $1):\n"
        f"Balance-kaaga: ${user['balance']:.2f}",
        reply_markup=kb
    )

    await dp.current_state(user=uid).set_state(WithdrawalState.waiting_local_number)


# ================= WITHDRAWAL CRYPTO =================
@dp.message(F.text == "CRYPTO")
async def withdrawal_crypto(msg: Message):
    uid = msg.from_user.id
    user = users.get(uid)
    if not user:
        await msg.answer("❌ User lama helin.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Back")]],
        resize_keyboard=True
    )

    await msg.answer(
        f"💰 Fadlan soo dir Address-ka crypto (Min $1):\n"
        f"Balance-kaaga: ${user['balance']:.2f}",
        reply_markup=kb
    )

    await dp.current_state(user=uid).set_state(WithdrawalState.waiting_crypto_address)


# ================= RECEIVE LOCAL NUMBER =================@dp.message(StateFilter(WithdrawalState.waiting_local_number))
async def receive_local_number(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    user = users.get(uid)

    if not user:
        await msg.answer("❌ User lama helin.")
        return

    number = msg.text.strip()

    if user.get('balance', 0) < 1:
        await msg.answer("❌ Balance-kaaga ma gaadhin $1. Waxaad u baahan tahay ugu yaraan $1.")
        return

    request_id = random.randint(10000, 99999)
    withdrawal_request = {
        "uid": uid,
        "type": "LOCAL",
        "amount": user['balance'],
        "number": number,
        "status": "Pending",
        "request_id": request_id
    }

    withdrawals[request_id] = withdrawal_request
    user['balance'] = 0  # balance-ka user automatic u isticmaalaa

    # Admin Notification
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{request_id}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{request_id}"),
            InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{request_id}")
        ]
    ])

    text = (
        f"💳 NEW WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${withdrawal_request['amount']:.2f}\n"
        f"🧾 Request ID: {request_id}\n"
        f"🏦 Number: {number}\n"
        f"⏳ Status: Pending"
    )

    await bot.send_message(ADMIN_ID, text, reply_markup=kb_admin)
    await msg.answer(
        f"✅ Withdrawal Request Sent\n"
        f"Request ID: {request_id}\n"
        f"Balance Left: ${user['balance']:.2f}"
    )

    await state.clear()


# ================= RECEIVE CRYPTO ADDRESS =================
@dp.message(StateFilter(WithdrawalState.waiting_crypto_address))
async def receive_crypto_address(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    user = users.get(uid)
    address = msg.text.strip()

    if user['balance'] < 1:
        await msg.answer("❌ Balance-kaaga ma gaadhin $1. Waxaad u baahan tahay ugu yaraan $1.")
        return

    request_id = random.randint(10000, 99999)
    withdrawal_request = {
        "uid": uid,
        "type": "CRYPTO",
        "amount": user['balance'],
        "address": address,
        "status": "Pending",
        "request_id": request_id
    }

    withdrawals[request_id] = withdrawal_request
    user['balance'] = 0

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{request_id}"),
         InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{request_id}"),
         InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{request_id}")]
    ])

    text = (
        f"💳 NEW WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${withdrawal_request['amount']:.2f}\n"
        f"🧾 Request ID: {request_id}\n"
        f"🏦 Address: {address}\n"
        f"⏳ Status: Pending"
    )

    await bot.send_message(ADMIN_ID, text, reply_markup=kb_admin)
    await msg.answer(f"✅ Withdrawal Request Sent\nRequest ID: {request_id}\nBalance Left: ${user['balance']:.2f}")
    await state.clear()


# ================= BACK BUTTON =================
@dp.message(F.text == "Back")
async def go_back(msg: Message):
    await start(msg)  # Dib ugu celin /start menu

# ================== ADMIN PANEL BUTTONS ==================
@dp.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ You are not authorized.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Stats"), KeyboardButton(text="Add Balance")],
            [KeyboardButton(text="Withdrawal Check")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await msg.answer("👑 Admin Panel:", reply_markup=kb)


# ================== STATS ==================
@dp.message(F.text == "Stats")
async def admin_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    total_users = len(users)
    total_balance = sum(u.get("balance", 0) for u in users.values())
    total_card_get = sum(1 for u in users.values() if u.get("type") == "card")
    total_virtual_get = sum(1 for u in users.values() if u.get("type") == "virtual")

    text = (
        f"📊 Admin Stats\n\n"
        f"Total Users: {total_users}\n"
        f"Total Balance: ${total_balance:.2f}\n"
        f"Total Card Orders: {total_card_get}\n"
        f"Total Virtual Orders: {total_virtual_get}"
    )

    await msg.answer(text)


# ================== ADD BALANCE ==================
class AdminAddBalance(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()

@dp.message(F.text == "Add Balance")
async def admin_add_balance(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer("📌 Geli Telegram ID-ga user-ka:")
    await dp.current_state(user=msg.from_user.id).set_state(AdminAddBalance.waiting_user_id)


@dp.message(StateFilter(AdminAddBalance.waiting_user_id))
async def receive_user_id(msg: Message, state: FSMContext):
    try:
        user_id = int(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli ID sax ah.")
        return

    await state.update_data(user_id=user_id)
    await msg.answer("📌 Geli Amount-ka lagu dari doono Balance:")
    await state.set_state(AdminAddBalance.waiting_amount)


@dp.message(StateFilter(AdminAddBalance.waiting_amount))
async def receive_amount(msg: Message, state: FSMContext):
    try:
        amount = float(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli Amount sax ah (tusaale: 1.5)")
        return

    data = await state.get_data()
    user_id = data.get("user_id")

    if user_id not in users:
        users[user_id] = {"balance": 0, "type": None}  # Haddii user cusub
    users[user_id]["balance"] = users[user_id].get("balance", 0) + amount

    await msg.answer(f"✅ User {user_id} Balance updated: ${users[user_id]['balance']:.2f}")
    await state.clear()


# ================== WITHDRAWAL CHECK ==================
@dp.message(F.text == "Withdrawal Check")
async def withdrawal_check(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    if not withdrawals:
        await msg.answer("❌ Ma jiraan codsiyo withdraw ah.")
        return

    for req_id, req in withdrawals.items():
        text = (
            f"💳 Withdrawal Request\n"
            f"👤 User: {req['uid']}\n"
            f"💵 Amount: ${req['amount']:.2f}\n"
            f"🧾 Request ID: {req_id}\n"
            f"🏦 {'Number: ' + req['number'] if req['type'] == 'LOCAL' else 'Address: ' + req['address']}\n"
            f"⏳ Status: {req['status']}"
        )

        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{req_id}"),
             InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{req_id}"),
             InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{req_id}")]
        ])

        await msg.answer(text, reply_markup=kb_admin)

# ================== WITHDRAWAL STORAGE ==================
withdrawals = {}
withdrawal_counter = 10000  # ID ga codsiyada si uu automatic u kordho


# ================== USER WITHDRAWAL ==================
@dp.message(F.text == "Withdrawal")
async def user_withdrawal(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="LOCAL"), KeyboardButton(text="CRYPTO")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await msg.answer("💸 Dooro Payment Method:", reply_markup=kb)


# ================== LOCAL WITHDRAWAL ==================
class WithdrawLocal(StatesGroup):
    waiting_amount = State()

@dp.message(F.text == "LOCAL")
async def withdrawal_local(msg: Message, state: FSMContext):
    await msg.answer(f"🤑 Soo dir Number-kaaga si lacagta laguu diro (min $1).")
    await state.set_state(WithdrawLocal.waiting_amount)


@dp.message(StateFilter(WithdrawLocal.waiting_amount))
async def receive_local_withdraw(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    amount_text = msg.text.strip()

    try:
        amount = float(amount_text)
    except:
        await msg.answer("❌ Fadlan geli amount sax ah (tusaale: 1.0)")
        return

    if amount < 1:
        await msg.answer("❌ Minimum amount waa $1")
        return

    balance = users.get(uid, {}).get("balance", 0)
    if amount > balance:
        await msg.answer(f"❌ Balance-gaaga ma filna. Current: ${balance:.2f}")
        return

    global withdrawal_counter
    withdrawal_counter += 1
    req_id = withdrawal_counter

    number = LOCAL_NUMBER  # user-ka waa inuu soo diraa Number-kan

    withdrawals[req_id] = {
        "uid": uid,
        "amount": amount,
        "type": "LOCAL",
        "number": number,
        "status": "Pending"
    }

    users[uid]["balance"] -= amount

    await msg.answer(
        f"✅ Withdrawal Request Sent\n"
        f"🧾 Request ID: {req_id}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🏦 Number: {number}\n"
        f"💰 Balance Left: ${users[uid]['balance']:.2f}\n"
        f"⏳ Status: Pending",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Back")]],
            resize_keyboard=True
        )
    )

    # Notify admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{req_id}"),
         InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{req_id}"),
         InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{req_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"💳 NEW WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🧾 Request ID: {req_id}\n"
        f"🏦 Number: {number}\n"
        f"⏳ Status: Pending",
        reply_markup=kb_admin
    )

    await state.clear()


# ================== CRYPTO WITHDRAWAL ==================
class WithdrawCrypto(StatesGroup):
    waiting_address = State()
    waiting_amount = State()

@dp.message(F.text == "CRYPTO")
async def withdrawal_crypto(msg: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="USDT-BEP20"), KeyboardButton(text="CANCEL")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
    await msg.answer("💰 Dooro Crypto:", reply_markup=kb)


@dp.message(F.text == "USDT-BEP20")
async def withdrawal_crypto_address(msg: Message, state: FSMContext):
    await msg.answer("📌 Soo dir Address-kaaga Crypto:")
    await state.set_state(WithdrawCrypto.waiting_address)


@dp.message(StateFilter(WithdrawCrypto.waiting_address))
async def receive_crypto_address(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    address = msg.text.strip()

    await state.update_data(address=address)
    await msg.answer("📌 Geli Amount-ka lagu bixinayo (min $1):")
    await state.set_state(WithdrawCrypto.waiting_amount)


@dp.message(StateFilter(WithdrawCrypto.waiting_amount))
async def receive_crypto_amount(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    data = await state.get_data()
    address = data.get("address")
    amount_text = msg.text.strip()

    try:
        amount = float(amount_text)
    except:
        await msg.answer("❌ Fadlan geli amount sax ah (tusaale: 1.0)")
        return

    if amount < 1:
        await msg.answer("❌ Minimum amount waa $1")
        return

    balance = users.get(uid, {}).get("balance", 0)
    if amount > balance:
        await msg.answer(f"❌ Balance-gaaga ma filna. Current: ${balance:.2f}")
        return

    global withdrawal_counter
    withdrawal_counter += 1
    req_id = withdrawal_counter

    withdrawals[req_id] = {
        "uid": uid,
        "amount": amount,
        "type": "CRYPTO",
        "address": address,
        "status": "Pending"
    }

    users[uid]["balance"] -= amount

    await msg.answer(
        f"✅ Withdrawal Request Sent\n"
        f"🧾 Request ID: {req_id}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🏦 Address: {address}\n"
        f"💰 Balance Left: ${users[uid]['balance']:.2f}\n"
        f"⏳ Status: Pending",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Back")]],
            resize_keyboard=True
        )
    )

    # Notify admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{req_id}"),
         InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{req_id}"),
         InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{req_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"💳 NEW WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🧾 Request ID: {req_id}\n"
        f"🏦 Address: {address}\n"
        f"⏳ Status: Pending",
        reply_markup=kb_admin
    )

    await state.clear()

# ================== ADMIN WITHDRAWAL HANDLING ==================

@dp.callback_query(F.data.startswith("admin_withdraw_confirm_"))
async def admin_withdraw_confirm(call: CallbackQuery):
    req_id = int(call.data.split("_")[-1])
    request = withdrawals.get(req_id)

    if not request:
        await call.message.edit_text("❌ Request not found.")
        return

    uid = request["uid"]
    request["status"] = "Paid"

    # Notify user
    await bot.send_message(
        uid,
        f"✅ Withdrawal Confirmed!\n"
        f"🧾 Request ID: {req_id}\n"
        f"💵 Amount: ${request['amount']:.2f}\n"
        f"⏳ Status: Paid"
    )

    await call.message.edit_text(f"✅ Withdrawal Request {req_id} Confirmed")


@dp.callback_query(F.data.startswith("admin_withdraw_reject_"))
async def admin_withdraw_reject(call: CallbackQuery):
    req_id = int(call.data.split("_")[-1])
    request = withdrawals.get(req_id)

    if not request:
        await call.message.edit_text("❌ Request not found.")
        return

    uid = request["uid"]
    request["status"] = "Rejected"

    # Refund balance
    if uid in users:
        users[uid]["balance"] += request["amount"]

    # Notify user
    await bot.send_message(
        uid,
        f"❌ Withdrawal Rejected!\n"
        f"🧾 Request ID: {req_id}\n"
        f"💵 Amount: ${request['amount']:.2f}\n"
        f"💰 Balance Restored: ${users[uid]['balance']:.2f}\n"
        f"⏳ Status: Rejected"
    )

    await call.message.edit_text(f"❌ Withdrawal Request {req_id} Rejected")


@dp.callback_query(F.data.startswith("admin_withdraw_ask_"))
async def admin_withdraw_ask(call: CallbackQuery):
    req_id = int(call.data.split("_")[-1])
    request = withdrawals.get(req_id)

    if not request:
        await call.message.edit_text("❌ Request not found.")
        return

    uid = request["uid"]

    await bot.send_message(
        uid,
        "ℹ️ Admin ayaa kula soo xiriiri doona si dalabkaaga loo dhamaystiro."
    )

    await call.message.edit_text(f"⚠️ Admin Requested User for Withdrawal {req_id}")

# ================== MAIN ==================
async def main():
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
