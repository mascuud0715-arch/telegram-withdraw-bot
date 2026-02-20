import asyncio
import os
import random
import sqlite3
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

ADMIN_ID = 7983838654
TZ = pytz.timezone("Africa/Mogadishu")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    full_name TEXT,
    bot_id TEXT,
    referral_code TEXT,
    referred_by TEXT,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    reward_count INTEGER DEFAULT 0,
    last_reward_date TEXT,
    is_banned INTEGER DEFAULT 0,
    joined_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    request_id INTEGER PRIMARY KEY,
    telegram_id INTEGER,
    amount REAL,
    address TEXT,
    network TEXT,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ================= UTILITIES =================

def now():
    return datetime.now(TZ)

def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")

def generate_ref():
    return str(random.randint(1000000000, 9999999999))

def generate_bot_id():
    return str(random.randint(10000000000, 99999999999))

def generate_request_id():
    return random.randint(10000, 99999)

def is_work_time():
    current = now()
    allowed_days = [5,6,0,1,2]  # Sat-Wed
    return current.weekday() in allowed_days and current.hour in [10,11]

def time_remaining():
    current = now()
    return f"Current time: {current.strftime('%H:%M')}"

def reset_weekly_rewards():
    week = now().isocalendar()[1]
    cursor.execute("SELECT telegram_id, last_reward_date FROM users")
    users = cursor.fetchall()
    for user in users:
        if user[1]:
            last_week = datetime.strptime(user[1], "%Y-%m-%d").isocalendar()[1]
            if last_week != week:
                cursor.execute("UPDATE users SET reward_count=0 WHERE telegram_id=?", (user[0],))
    conn.commit()

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):
    reset_weekly_rewards()

    user_id = message.from_user.id
    full_name = message.from_user.full_name
    args = message.text.split()

    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        ref_used = args[1] if len(args) > 1 else None

        cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            full_name,
            generate_bot_id(),
            generate_ref(),
            ref_used,
            15,
            0,
            0,
            None,
            0,
            now_str()
        ))
        conn.commit()

        # Referral reward
        if ref_used:
            cursor.execute("SELECT telegram_id FROM users WHERE referral_code=?", (ref_used,))
            owner = cursor.fetchone()
            if owner:
                bonus = 10 if is_work_time() else 1
                cursor.execute("UPDATE users SET balance=balance+?, referrals=referrals+1 WHERE telegram_id=?",
                               (bonus, owner[0]))
                conn.commit()

        await message.answer("🎉 Welcome! You received $15 bonus.")

    await message.answer("🤖 Bot Ready.")

# ================= PROFILE =================

@dp.message(Command("profile"))
async def profile(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT bot_id, balance, referrals, referral_code FROM users WHERE telegram_id=?", (user_id,))
    data = cursor.fetchone()
    if not data:
        return

    bot_id, balance, refs, ref_code = data
    me = await bot.get_me()

    await message.answer(f"""
👤 ID: {user_id}
🤖 BOT ID: {bot_id}
💰 Balance: ${balance}
👥 Referrals: {refs}

🔗 Referral:
https://t.me/{me.username}?start={ref_code}
""")

# ================= REWARD =================

@dp.message(Command("reward"))
async def reward(message: types.Message):
    reset_weekly_rewards()
    user_id = message.from_user.id

    if not is_work_time():
        await message.answer(f"⏳ Wait next day.\n{time_remaining()}")
        return

    today = now().strftime("%Y-%m-%d")

    cursor.execute("SELECT reward_count, last_reward_date FROM users WHERE telegram_id=?", (user_id,))
    reward_count, last_date = cursor.fetchone()

    if last_date == today:
        await message.answer("❌ Already claimed today.")
        return

    if reward_count >= 5:
        await message.answer("❌ Weekly limit reached.")
        return

    cursor.execute("""
    UPDATE users SET balance=balance+50,
    reward_count=reward_count+1,
    last_reward_date=? WHERE telegram_id=?
    """, (today, user_id))

    conn.commit()
    await message.answer("🎉 Reward received: $50")

# ================= WITHDRAW =================

@dp.message(Command("withdraw"))
async def withdraw(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT-BEP20", callback_data="net_usdt")],
        [InlineKeyboardButton(text="BNB", callback_data="net_bnb")]
    ])
    await message.answer("Choose Network:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("net_"))
async def choose_network(callback: types.CallbackQuery):
    network = callback.data.split("_")[1]
    await callback.message.answer("Send: amount address\nExample:\n100 0xAddress")
    dp.message.register(lambda msg: process_withdraw(msg, network))
    await callback.answer()

async def process_withdraw(message: types.Message, network):
    try:
        amount, address = message.text.split()
        amount = float(amount)
    except:
        await message.answer("Invalid format")
        return

    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (user_id,))
    balance = cursor.fetchone()[0]

    if amount < 100:
        await message.answer("Minimum $100")
        return

    if balance < amount:
        await message.answer("Insufficient balance")
        return

    request_id = generate_request_id()

    cursor.execute("UPDATE users SET balance=balance-? WHERE telegram_id=?", (amount, user_id))
    cursor.execute("""
    INSERT INTO withdrawals VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (request_id, user_id, amount, address, network.upper(), "Pending", now_str()))
    conn.commit()

    await message.answer(f"""
✅ Withdrawal Sent
🧾 ID: {request_id}
💵 ${amount}
🏦 {address}
⏳ Pending
""")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CONFIRM", callback_data=f"confirm_{request_id}"),
            InlineKeyboardButton(text="REJECT", callback_data=f"reject_{request_id}"),
            InlineKeyboardButton(text="BAN", callback_data=f"ban_{user_id}")
        ]
    ])

    await bot.send_message(ADMIN_ID, f"NEW WITHDRAW\nID:{request_id}\nUser:{user_id}\nAmount:${amount}", reply_markup=keyboard)

# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 STATS", callback_data="stats")],
        [InlineKeyboardButton(text="🔎 WITHDRAW CHECK", callback_data="check")],
        [InlineKeyboardButton(text="♻️ UNBAN", callback_data="unban")]
    ])
    await message.answer("ADMIN PANEL", reply_markup=keyboard)

@dp.callback_query(F.data == "stats")
async def stats(callback: types.CallbackQuery):
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned=1")
    banned = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM withdrawals WHERE status='Approved'")
    total_paid = cursor.fetchone()[0] or 0

    await callback.message.answer(f"""
📊 STATS
Users: {total_users}
Active: {total_users-banned}
Banned: {banned}
Total Balance: ${round(total_balance,2)}
Total Paid: ${round(total_paid,2)}
""")

    await callback.answer()

# ================= RUN =================

async def main():
    print("Bot Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
