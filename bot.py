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

url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables!")

ADMIN_ID = 7983838654

LOCAL_NUMBER = "+252907868526"
BNB_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
USDT_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())

# ================= DATA STORAGE =================
users = {}
withdrawals = {}
stats = {
    "total_users": 0,
    "total_virtual": 0,
    "total_card": 0
}
withdrawal_counter = 10000

# ================= STATES =================
class VirtualState(StatesGroup):
    waiting_screenshot = State()

class CardState(StatesGroup):
    screenshot = State()

class WithdrawalState(StatesGroup):
    waiting_local_number = State()
    waiting_crypto_address = State()

class AdminAddBalanceState(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()

class WithdrawLocal(StatesGroup):
    waiting_amount = State()

class WithdrawCrypto(StatesGroup):
    waiting_address = State()
    waiting_amount = State()

# ================= HELPERS =================
def random_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

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

    if uid == ADMIN_ID:
        kb.keyboard.append([KeyboardButton(text="Admin Panel")])

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
    text += f"Number of referrals: {len(ref_list)}\n\n"
    text += "Referred Users:\n"

    for r in ref_list:
        text += f"- {r}\n"

    await msg.answer(text)

# ================= WITHDRAWAL MENU =================
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

# ================= STATS =================
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

# ================= ADMIN ADD BALANCE =================
@dp.message(F.text == "Add Balance")
async def admin_add_balance(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return

    await msg.answer("📌 Geli Telegram ID-ga user-ka:")
    await state.set_state(AdminAddBalanceState.waiting_user_id)


@dp.message(StateFilter(AdminAddBalanceState.waiting_user_id))
async def receive_user_id(msg: Message, state: FSMContext):
    try:
        user_id = int(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli ID sax ah.")
        return

    await state.update_data(user_id=user_id)
    await msg.answer("📌 Geli Amount-ka lagu dari doono Balance:")
    await state.set_state(AdminAddBalanceState.waiting_amount)


@dp.message(StateFilter(AdminAddBalanceState.waiting_amount))
async def receive_amount(msg: Message, state: FSMContext):
    try:
        amount = float(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli Amount sax ah (tusaale: 1.5)")
        return

    data = await state.get_data()
    user_id = data.get("user_id")

    if user_id not in users:
        users[user_id] = {
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

    users[user_id]["balance"] += amount

    await msg.answer(
        f"✅ User {user_id} Balance updated: ${users[user_id]['balance']:.2f}"
    )

    await state.clear()


# ================= WITHDRAWAL CHECK (ADMIN) =================
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
            [
                InlineKeyboardButton(
                    text="CONFIRM",
                    callback_data=f"admin_withdraw_confirm_{req_id}"
                ),
                InlineKeyboardButton(
                    text="REJECT",
                    callback_data=f"admin_withdraw_reject_{req_id}"
                ),
                InlineKeyboardButton(
                    text="ASK",
                    callback_data=f"admin_withdraw_ask_{req_id}"
                )
            ]
        ])

        await msg.answer(text, reply_markup=kb_admin)

# ================= LOCAL WITHDRAWAL =================
@dp.message(F.text == "LOCAL")
async def withdrawal_local(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    user = users.get(uid)

    if not user:
        await msg.answer("❌ User lama helin.")
        return

    await msg.answer("📌 Geli amount-ka aad rabto inaad la baxdo (min $1):")
    await state.set_state(WithdrawLocal.waiting_amount)


@dp.message(StateFilter(WithdrawLocal.waiting_amount))
async def receive_local_withdraw(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    user = users.get(uid)

    if not user:
        await msg.answer("❌ User lama helin.")
        return

    try:
        amount = float(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli amount sax ah (tusaale: 1.0)")
        return

    if amount < 1:
        await msg.answer("❌ Minimum amount waa $1")
        return

    balance = user.get("balance", 0)

    if amount > balance:
        await msg.answer(f"❌ Balance-gaaga ma filna. Current: ${balance:.2f}")
        return

    global withdrawal_counter
    withdrawal_counter += 1
    req_id = withdrawal_counter

    number = LOCAL_NUMBER

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

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="CONFIRM",
                callback_data=f"admin_withdraw_confirm_{req_id}"
            ),
            InlineKeyboardButton(
                text="REJECT",
                callback_data=f"admin_withdraw_reject_{req_id}"
            ),
            InlineKeyboardButton(
                text="ASK",
                callback_data=f"admin_withdraw_ask_{req_id}"
            )
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"💳 NEW LOCAL WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🧾 Request ID: {req_id}\n"
        f"🏦 Number: {number}\n"
        f"⏳ Status: Pending",
        reply_markup=kb_admin
    )

    await state.clear()

# ================= CRYPTO WITHDRAWAL =================
@dp.message(F.text == "CRYPTO")
async def withdrawal_crypto(msg: Message):
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
    address = msg.text.strip()

    if len(address) < 10:
        await msg.answer("❌ Address ma saxna.")
        return

    await state.update_data(address=address)
    await msg.answer("📌 Geli Amount-ka lagu bixinayo (min $1):")
    await state.set_state(WithdrawCrypto.waiting_amount)


@dp.message(StateFilter(WithdrawCrypto.waiting_amount))
async def receive_crypto_amount(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    user = users.get(uid)

    if not user:
        await msg.answer("❌ User lama helin.")
        return

    data = await state.get_data()
    address = data.get("address")

    try:
        amount = float(msg.text.strip())
    except:
        await msg.answer("❌ Fadlan geli amount sax ah (tusaale: 1.0)")
        return

    if amount < 1:
        await msg.answer("❌ Minimum amount waa $1")
        return

    balance = user.get("balance", 0)

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

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="CONFIRM",
                callback_data=f"admin_withdraw_confirm_{req_id}"
            ),
            InlineKeyboardButton(
                text="REJECT",
                callback_data=f"admin_withdraw_reject_{req_id}"
            ),
            InlineKeyboardButton(
                text="ASK",
                callback_data=f"admin_withdraw_ask_{req_id}"
            )
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"💳 NEW CRYPTO WITHDRAWAL\n\n"
        f"👤 User: {uid}\n"
        f"💵 Amount: ${amount:.2f}\n"
        f"🧾 Request ID: {req_id}\n"
        f"🏦 Address: {address}\n"
        f"⏳ Status: Pending",
        reply_markup=kb_admin
    )

    await state.clear()

# ================== ADMIN WITHDRAWAL CALLBACKS ==================
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


# ================== REFERRAL SYSTEM HOOK ==================
def add_referral(user_id: int, ref_code: str):
    """Add referral user if ref_code exists"""
    for uid, data in users.items():
        if data.get("ref_code") == ref_code:
            if user_id not in data["referrals"]:
                data["referrals"].append(user_id)
                # Optionally, add bonus balance
                data["balance"] += 0.5  # Example bonus
            break


@dp.message(lambda m: m.text and m.text.startswith("/ref "))
async def referral_handler(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("❌ Usage: /ref <referral_code>")
        return

    ref_code = parts[1].strip()
    uid = msg.from_user.id

    add_referral(uid, ref_code)
    await msg.answer(f"✅ Referral code applied: {ref_code}")

# ================== ADMIN PANEL & BACK BUTTON ==================
@dp.message(F.text == "Back")
async def back_to_main(msg: Message):
    uid = msg.from_user.id
    if uid == ADMIN_ID:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Stats"), KeyboardButton(text="Add Balance")],
                [KeyboardButton(text="Withdrawal Check")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )
        await msg.answer("⚙️ Admin Panel:", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Balance"), KeyboardButton(text="Referral")],
                [KeyboardButton(text="Withdrawal")]
            ],
            resize_keyboard=True
        )
        await msg.answer("Ku soo dhawoow Service Bot 🤖\nDooro waxa aad rabto:", reply_markup=kb)


# ================== USER MENU BUTTONS ==================
@dp.message(F.text == "Start Over")
async def restart_menu(msg: Message):
    await start(msg)


# ================== INLINE BUTTON NAVIGATION ==================
@dp.callback_query(F.data == "check_balance")
async def inline_check_balance(call: CallbackQuery):
    uid = call.from_user.id
    user = users.get(uid)
    if not user:
        await call.message.edit_text("❌ User lama helin.")
        return
    await call.message.edit_text(f"💰 Balance-kaaga hadda: ${user['balance']:.2f}")


@dp.callback_query(F.data == "show_referrals")
async def inline_show_referrals(call: CallbackQuery):
    uid = call.from_user.id
    user = users.get(uid)
    if not user:
        await call.message.edit_text("❌ User lama helin.")
        return

    ref_list = user.get("referrals", [])
    text = f"👥 Referral Code: {user['ref_code']}\n"
    text += f"Number of referrals: {len(ref_list)}\n"
    text += "\nReferred Users:\n"
    for r in ref_list:
        text += f"- {r}\n"
    await call.message.edit_text(text)


# ================== ADMIN INLINE NAVIGATION ==================
@dp.callback_query(F.data == "admin_stats")
async def inline_admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
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
    await call.message.edit_text(text)


@dp.callback_query(F.data == "admin_add_balance")
async def inline_admin_add_balance(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.edit_text("📌 Geli Telegram ID-ga user-ka:")
    await dp.current_state(user=call.from_user.id).set_state(AdminAddBalance.waiting_user_id)


# ================== HELPER FUNCTIONS FOR INLINE KEYBOARDS ==================
def main_user_inline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Check Balance", callback_data="check_balance")],
        [InlineKeyboardButton(text="Referral", callback_data="show_referrals")]
    ])


def main_admin_inline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Add Balance", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="Withdrawal Check", callback_data="admin_withdraw_check")]
    ])


# ================== ADMIN INLINE WITHDRAW CHECK ==================
@dp.callback_query(F.data == "admin_withdraw_check")
async def inline_admin_withdraw_check(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    if not withdrawals:
        await call.message.edit_text("❌ Ma jiraan codsiyo withdraw ah.")
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
            [
                InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_withdraw_confirm_{req_id}"),
                InlineKeyboardButton(text="REJECT", callback_data=f"admin_withdraw_reject_{req_id}"),
                InlineKeyboardButton(text="ASK", callback_data=f"admin_withdraw_ask_{req_id}")
            ]
        ])

        await call.message.answer(text, reply_markup=kb_admin)


# ================== MAIN ENTRY POINT ==================
async def main():
    logging.info("Bot is starting...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot encountered an error: {e}")


# ================== RUN BOT ==================
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
