import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.filters import Command

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= NUMBER GENERATORS =================

def generate_virtual_number():
    return "063" + "".join(str(random.randint(0, 9)) for _ in range(7))

def generate_vip_number():
    return "06349" + "".join(str(random.randint(0, 9)) for _ in range(5))

# ================= START =================

@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await message.answer("Ku soo dhawoow Telesom Bot", reply_markup=keyboard)

# ================= VIRTUAL =================

@dp.callback_query(F.data == "virtual")
async def virtual_menu(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton(text="TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton(text="GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro adeeg:", reply_markup=keyboard)

@dp.callback_query(F.data.in_(["whatsapp", "tiktok", "telegram", "google"]))
async def show_virtual_number(call: CallbackQuery):
    number = generate_virtual_number()
    keyboard = payment_keyboard()
    await call.message.edit_text(
        f"Number-kaaga:\n{number}\n\nQiimaha: $1\n\nPlease Send Money",
        reply_markup=keyboard
    )
    await notify_admin(call.from_user.id, "Virtual", number)

# ================= CARD =================

@dp.callback_query(F.data == "card")
async def card_menu(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro nooca Card:", reply_markup=keyboard)

@dp.callback_query(F.data == "vip")
async def vip_card(call: CallbackQuery):
    numbers = "\n".join(generate_vip_number() for _ in range(3))
    keyboard = payment_keyboard()
    await call.message.edit_text(
        f"VIP Numbers:\n{numbers}\n\nQiimaha: $15\n\nPlease Send Money",
        reply_markup=keyboard
    )
    await notify_admin(call.from_user.id, "VIP", numbers)

@dp.callback_query(F.data == "normal")
async def normal_card(call: CallbackQuery):
    number = generate_virtual_number()
    keyboard = payment_keyboard()
    await call.message.edit_text(
        f"Number-kaaga:\n{number}\n\nQiimaha: $1\n\nPlease Send Money",
        reply_markup=keyboard
    )
    await notify_admin(call.from_user.id, "Normal Card", number)

# ================= PAYMENT =================

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL PAYMENT", callback_data="local")],
        [InlineKeyboardButton(text="CRYPTO CURRENCY", callback_data="crypto")]
    ])

@dp.callback_query(F.data == "local")
async def local_payment(call: CallbackQuery):
    await call.message.answer("Fadlan lacag ku dir:\n+252907868526")

@dp.callback_query(F.data == "crypto")
async def crypto_menu(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT-BEP20", callback_data="usdt")],
        [InlineKeyboardButton(text="BNB", callback_data="bnb")]
    ])
    await call.message.answer("Dooro Crypto:", reply_markup=keyboard)

@dp.callback_query(F.data == "usdt")
async def usdt_address(call: CallbackQuery):
    await call.message.answer(
        "USDT-BEP20 Address:\n0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    )

@dp.callback_query(F.data == "bnb")
async def bnb_address(call: CallbackQuery):
    await call.message.answer(
        "BNB Address:\n0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    )

# ================= ADMIN SYSTEM =================

async def notify_admin(user_id, order_type, number):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"confirm_{user_id}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{user_id}")],
        [InlineKeyboardButton(text="BAN", callback_data=f"ban_{user_id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"New Order\n\nUser ID: {user_id}\nType: {order_type}\nNumber(s):\n{number}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Payment Confirmed ✅")
    await call.message.edit_text("Order Confirmed")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Payment Rejected ❌")
    await call.message.edit_text("Order Rejected")

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "You are Banned ❌")
    await call.message.edit_text("User Banned")

# ================= RUN BOT =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
