import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ====== TEMP STORAGE ======
user_orders = {}

# ====== NUMBER GENERATORS ======

def generate_virtual_number():
    return "063" + "".join(str(random.randint(0, 9)) for _ in range(7))

def generate_vip_number():
    return "06349" + "".join(str(random.randint(0, 9)) for _ in range(5))

# ====== START ======

@dp.message(Command("start"))
async def start_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await message.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ====== VIRTUAL ======

@dp.callback_query(F.data == "virtual")
async def virtual_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton(text="TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton(text="GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro adeeg:", reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp", "tiktok", "telegram", "google"]))
async def virtual_selected(call: CallbackQuery):
    number = generate_virtual_number()

    user_orders[call.from_user.id] = {
        "type": "Virtual",
        "number": number,
        "price": "$1"
    }

    kb = payment_keyboard()
    await call.message.edit_text(
        f"Number-kaaga:\n{number}\n\n"
        f"PLEASE SEND MONEY BEFORE\n"
        f"AND GET YOUR VIRTUAL CARD 💵",
        reply_markup=kb
    )

# ====== CARD ======

@dp.callback_query(F.data == "card")
async def card_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP", callback_data="vip")],
        [InlineKeyboardButton(text="normal", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro nooca Card:", reply_markup=kb)

@dp.callback_query(F.data == "vip")
async def vip_selected(call: CallbackQuery):
    numbers = "\n".join(generate_vip_number() for _ in range(3))

    user_orders[call.from_user.id] = {
        "type": "VIP",
        "number": numbers,
        "price": "$15"
    }

    kb = payment_keyboard()
    await call.message.edit_text(
        f"VIP Numbers:\n{numbers}\n\n"
        f"PLEASE SEND MONEY BEFORE\n"
        f"AND GET YOUR VIP CARD 💵",
        reply_markup=kb
    )

@dp.callback_query(F.data == "normal")
async def normal_selected(call: CallbackQuery):
    number = generate_virtual_number()

    user_orders[call.from_user.id] = {
        "type": "Normal",
        "number": number,
        "price": "$1"
    }

    kb = payment_keyboard()
    await call.message.edit_text(
        f"Number-kaaga:\n{number}\n\n"
        f"PLEASE SEND MONEY BEFORE\n"
        f"AND GET YOUR NORMAL CARD 💵",
        reply_markup=kb
    )

# ====== PAYMENT ======

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL PAYMENT", callback_data="local")],
        [InlineKeyboardButton(text="CRYPTO CURRENCY", callback_data="crypto")]
    ])

@dp.callback_query(F.data == "local")
async def local_payment(call: CallbackQuery):
    await call.message.answer("Fadlan lacag ku dir:\n+252907868526")

    await send_admin_request(call.from_user.id)

@dp.callback_query(F.data == "crypto")
async def crypto_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT-BEP20", callback_data="usdt")],
        [InlineKeyboardButton(text="BNB", callback_data="bnb")]
    ])
    await call.message.answer("Dooro Crypto:", reply_markup=kb)

    await send_admin_request(call.from_user.id)

# ====== ADMIN REQUEST ======

async def send_admin_request(user_id):
    if user_id not in user_orders:
        return

    order = user_orders[user_id]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"confirm_{user_id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{user_id}")],
        [InlineKeyboardButton(text="BAN", callback_data=f"ban_{user_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"NEW ORDER\n\n"
        f"User ID: {user_id}\n"
        f"Type: {order['type']}\n"
        f"Number:\n{order['number']}\n"
        f"Price: {order['price']}",
        reply_markup=kb
    )

# ====== ADMIN ACTIONS ======

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Payment Confirmed ✅")
    await call.message.edit_text("Confirmed")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Payment Rejected ❌")
    await call.message.edit_text("Rejected")

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "You are Banned ❌")
    await call.message.edit_text("User Banned")

# ====== RUN ======

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
