import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import datetime
import telebot
from telebot import types, apihelper
from config import BOT_TOKEN, ADMIN_ID, DRIVER_GROUP_ID, APP_NAME
from database import get_db, init_db

# Configure network resilience
apihelper.RETRY_ON_ERROR = True
apihelper.CONNECT_TIMEOUT = 25
apihelper.READ_TIMEOUT = 30

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# In-memory conversation state for Admin steps
admin_states = {}

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Statistika"),
        types.KeyboardButton("🚖 Zakazlar"),
        types.KeyboardButton("🛣 Yo'nalishlar"),
        types.KeyboardButton("🏷 Kuponlar"),
        types.KeyboardButton("👨‍✈️ Haydovchilar"),
        types.KeyboardButton("📢 Yangiliklar"),
        types.KeyboardButton("📨 Murojaatlar")
    )
    return markup

@bot.message_handler(commands=["start"])
def handle_start(message):
    try:
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            bot.send_message(
                message.chat.id,
                f"👑 <b>Xush kelibsiz, Bosh Admin!</b>\n\n"
                f"<b>{APP_NAME}</b> boshqaruv panelidasiz.\n"
                f"Kerakli bo'limni tanlang:",
                reply_markup=get_admin_keyboard()
            )
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📢 Haydovchilar guruhi", url="https://t.me/+cR_52L3bFmowMDli")
            )
            bot.send_message(
                message.chat.id,
                f"🚖 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
                f"Siz <b>{APP_NAME}</b> tizimidagi haydovchilar botidasiz.\n"
                f"Barcha yo'lovchi buyurtmalari haydovchilar guruhiga yuboriladi.\n"
                f"Guruhdagi <b>'Zakazni ko'rish / Qabul qilish'</b> tugmasi orqali buyurtmalarni qabul qilishingiz mumkin.",
                reply_markup=markup
            )
    except Exception as e:
        print(f"Error in handle_start: {e}")

# 📊 STATISTIKA
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "📊 Statistika")
def admin_stats(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total, SUM(final_price) as sum_price FROM orders")
    row_all = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as pending FROM orders WHERE status = 'pending'")
    row_pending = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as accepted FROM orders WHERE status = 'accepted'")
    row_accepted = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as routes_count FROM routes WHERE is_active = 1")
    row_routes = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as coupons_count FROM coupons WHERE is_active = 1")
    row_coupons = cursor.fetchone()
    conn.close()

    total_orders = row_all["total"] or 0
    total_rev = row_all["sum_price"] or 0
    pending_orders = row_pending["pending"] or 0
    accepted_orders = row_accepted["accepted"] or 0
    routes_count = row_routes["routes_count"] or 0
    coupons_count = row_coupons["coupons_count"] or 0

    text = (
        f"📊 <b>{APP_NAME} TIZIMI STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Jami buyurtmalar: <b>{total_orders} ta</b>\n"
        f"⏳ Kutilayotgan zakazlar: <b>{pending_orders} ta</b>\n"
        f"✅ Qabul qilingan zakazlar: <b>{accepted_orders} ta</b>\n"
        f"💵 Jami aylanma summa: <b>{total_rev:,} so'm</b>\n"
        f"🛣 Faol yo'nalishlar: <b>{routes_count} ta</b>\n"
        f"🎟 Faol kuponlar: <b>{coupons_count} ta</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, text)

# 🚖 ZAKAZLAR
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "🚖 Zakazlar")
def admin_orders(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 8")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "📭 Hozircha hech qanday buyurtma mavjud emas.")
        return

    bot.send_message(message.chat.id, "🚖 <b>Oxirgi buyurtmalar ro'yxati:</b>")
    for r in rows:
        status_badge = "⏳ Kutilmoqda" if r["status"] == "pending" else ("✅ Qabul qilingan" if r["status"] == "accepted" else "❌ Bekor qilingan")
        msg = (
            f"<b>Zakaz #{r['order_code']}</b> ({status_badge})\n"
            f"👤 Mijoz: <b>{r['passenger_name']}</b> (<code>{r['passenger_phone']}</code>)\n"
            f"📍 {r['route_title']} | {r['tariff'].upper()}\n"
            f"👥 {r['passengers_count']} kishi | 💰 <b>{r['final_price']:,} so'm</b>\n"
            f"🕒 {r['created_at']}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_order_{r['id']}")
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup)

# 🛣 YO'NALISHLAR (FULL CRUD)
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text in ["🛣 Yo'nalishlar", "🛣 Yo'nalish va Narxlar"])
def admin_routes_list(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routes WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Yangi yo'nalish qo'shish", callback_data="add_new_route"))
        bot.send_message(message.chat.id, "🛣 <b>Hozircha hech qanday yo'nalish kiritilmagan.</b>", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "🛣 <b>Mavjud yo'nalishlar boshqaruvi:</b>")
    for r in rows:
        duration_val = r['duration_hours'] if 'duration_hours' in r.keys() and r['duration_hours'] else "Noma'lum"
        text = (
            f"📍 <b>{r['title']}</b>\n"
            f"⏱ Safar vaqti: <b>{duration_val}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"• 🚗 Standart: <b>{r['price_standart']:,} so'm</b>\n"
            f"• 🚙 Camfort: <b>{r['price_camfort']:,} so'm</b>\n"
            f"• 🚘 Biznes: <b>{r['price_biznes']:,} so'm</b>"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✏️ Narxlarni tahrirlash", callback_data=f"edit_r_{r['id']}"),
            types.InlineKeyboardButton("⏱ Vaqtni tahrirlash", callback_data=f"edit_dur_{r['id']}"),
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_r_{r['id']}")
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)

    add_markup = types.InlineKeyboardMarkup()
    add_markup.add(types.InlineKeyboardButton("➕ Yangi yo'nalish qo'shish", callback_data="add_new_route"))
    bot.send_message(message.chat.id, "Yangi yo'nalish qo'shish uchun tugmani bosing:", reply_markup=add_markup)

# 🏷 KUPONLAR (FULL CRUD)
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text in ["🏷 Kuponlar", "🏷 Yangi Kupon"])
def admin_coupons_list(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Yangi kupon yaratish", callback_data="add_new_coupon"))
        bot.send_message(message.chat.id, "🏷 <b>Hozircha faol chegirma kuponlari mavjud emas.</b>", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "🏷 <b>Faol kuponlar boshqaruvi:</b>")
    for c in rows:
        text = (
            f"🏷 Kod: <code>{c['code']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Chegirma narxi: <b>{c['discount_amount']:,} so'm</b>\n"
            f"⏳ Amal qilish muddati: <b>{c['expiry_date']}</b>"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✏️ Narxni o'zgartirish", callback_data=f"edit_c_{c['id']}"),
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_c_{c['id']}")
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)

    add_markup = types.InlineKeyboardMarkup()
    add_markup.add(types.InlineKeyboardButton("➕ Yangi kupon yaratish", callback_data="add_new_coupon"))
    bot.send_message(message.chat.id, "Yangi kupon yaratish uchun tugmani bosing:", reply_markup=add_markup)

# 👨‍✈️ HAYDOVCHILAR (FULL CRUD)
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text in ["👨‍✈️ Haydovchilar", "Haydovchilar"])
def admin_drivers_list(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Yangi haydovchi qo'shish", callback_data="add_new_driver"))
        bot.send_message(message.chat.id, "👨‍✈️ <b>Hozircha tizimda haydovchilar ro'yxati bo'sh.</b>", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "👨‍✈️ <b>Tajribali haydovchilar ro'yxati (Mobil ilovada ko'rinadi):</b>")
    for d in rows:
        car_num = d['car_number'] if d['car_number'] else "Noma'lum"
        features = d['car_features'] if d['car_features'] else "Standart"
        text = (
            f"👤 <b>{d['name']}</b>\n"
            f"📞 Tel: <code>{d['phone']}</code>\n"
            f"🚘 Mashina: <b>{d['car_model']}</b> ({car_num})\n"
            f"⭐ Reyting: <b>{d['rating']}</b> | 🏁 Safarlar: <b>{d['trips_count']} ta</b>\n"
            f"✨ Qulayliklar: {features}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_drv_{d['id']}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    add_markup = types.InlineKeyboardMarkup()
    add_markup.add(types.InlineKeyboardButton("➕ Yangi haydovchi qo'shish", callback_data="add_new_driver"))
    bot.send_message(message.chat.id, "Yangi haydovchi qo'shish uchun tugmani bosing:", reply_markup=add_markup)

# 📢 YANGILIKLAR (FULL CRUD)
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text in ["📢 Yangiliklar", "📢 Yangilik Qo'shish"])
def admin_news_list(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Yangi yangilik qo'shish", callback_data="add_new_news"))
        bot.send_message(message.chat.id, "📢 <b>Hozircha yangiliklar joylanmagan.</b>", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "📢 <b>Ilovadagi yangiliklar & aksiyalar ro'yxati:</b>")
    for n in rows:
        text = (
            f"📢 <b>{n['title']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 {n['subtitle']}\n"
            f"🏷 Belgisi: {n['badge']} | 🕒 {n['created_at']}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_n_{n['id']}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    add_markup = types.InlineKeyboardMarkup()
    add_markup.add(types.InlineKeyboardButton("➕ Yangi yangilik qo'shish", callback_data="add_new_news"))
    bot.send_message(message.chat.id, "Yangi aksiya / yangilik qo'shish uchun tugmani bosing:", reply_markup=add_markup)

# 📨 MUROJAATLAR
@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "📨 Murojaatlar")
def admin_support_tickets(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM support_tickets ORDER BY id DESC LIMIT 6")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "📭 Mijozlar murojaatlari mavjud emas.")
        return

    bot.send_message(message.chat.id, "📨 <b>Oxirgi mijozlar murojaatlari:</b>")
    for r in rows:
        st = "🟢 Ochiq" if r["status"] == "open" else "⚪️ Javob berilgan"
        msg = (
            f"<b>Murojaat #{r['id']}</b> ({st})\n"
            f"👤 Mijoz: <b>{r['passenger_name']}</b> (<code>{r['passenger_phone']}</code>)\n"
            f"💬 Xabar: {r['message']}\n"
            f"🕒 {r['created_at']}"
        )
        markup = types.InlineKeyboardMarkup()
        if r["status"] == "open":
            markup.add(types.InlineKeyboardButton("✍️ Javob yozish", callback_data=f"reply_ticket_{r['id']}"))
        bot.send_message(message.chat.id, msg, reply_markup=markup)

# 📸 SPECIAL HANDLER: Photo Upload for News Image
@bot.message_handler(content_types=['photo'], func=lambda msg: msg.from_user.id == ADMIN_ID and msg.from_user.id in admin_states and admin_states[msg.from_user.id].get("step") == "news_img")
def handle_news_photo(message):
    state = admin_states[message.from_user.id]
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO news (title, subtitle, badge, image_url, created_at)
            VALUES (?, ?, 'YANGI', ?, ?)
        """, (state["title"], state["sub"], img_url, created_at))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            f"✅ <b>Rasm va Yangilik ilovaga muvaffaqiyatli joylandi!</b>\n\n"
            f"📰 Sarlavha: <b>{state['title']}</b>\n"
            f"📝 Tavsif: {state['sub']}\n"
            f"🖼 Rasm saqlandi va ilovada ko'rsatiladi.",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Rasm yuklashda xatolik: {e}")
        del admin_states[message.from_user.id]

# 📸 SPECIAL HANDLER: Photo Upload for Driver Image
@bot.message_handler(content_types=['photo'], func=lambda msg: msg.from_user.id == ADMIN_ID and msg.from_user.id in admin_states and admin_states[msg.from_user.id].get("step") == "driver_photo")
def handle_driver_photo(message):
    state = admin_states[message.from_user.id]
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drivers (name, phone, car_model, car_number, rating, trips_count, image_url, car_features, is_active)
            VALUES (?, ?, ?, ?, 5.0, 100, ?, ?, 1)
        """, (state["name"], state["phone"], state["car_model"], state.get("car_number", ""), img_url, state.get("features", "Konditsioner, Shinam salon")))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]

        bot.send_message(
            message.chat.id,
            f"✅ <b>Haydovchi muvaffaqiyatli qo'shildi!</b>\n\n"
            f"👤 Ism: <b>{state['name']}</b>\n"
            f"📞 Tel: <b>{state['phone']}</b>\n"
            f"🚘 Mashina: <b>{state['car_model']}</b>\n"
            f"🖼 Rasm saqlandi va mobil ilovada ko'rinadi.",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Rasm yuklashda xatolik: {e}")
        del admin_states[message.from_user.id]

# 📝 MULTI-STEP ADMIN CONVERSATION FLOW
@bot.message_handler(content_types=['text'], func=lambda msg: msg.from_user.id == ADMIN_ID and msg.from_user.id in admin_states)
def handle_admin_text_steps(message):
    state = admin_states[message.from_user.id]
    step = state.get("step")

    # 1. Edit Route Price Flow
    if step == "edit_route_price_input":
        try:
            new_price = int(message.text.replace(" ", ""))
            route_id = state["route_id"]
            tariff_col = state["tariff_col"]
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE routes SET {tariff_col} = ? WHERE id = ?", (new_price, route_id))
            conn.commit()
            conn.close()
            del admin_states[message.from_user.id]
            bot.send_message(message.chat.id, f"✅ <b>Tarif narxi {new_price:,} so'm ga muvaffaqiyatli o'zgartirildi!</b>", reply_markup=get_admin_keyboard())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Iltimos faqat raqam kiriting (masalan: 120000):")

    # 1.1 Edit Route Duration Flow
    elif step == "edit_route_duration_input":
        new_dur = message.text.strip()
        route_id = state["route_id"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE routes SET duration_hours = ? WHERE id = ?", (new_dur, route_id))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]
        bot.send_message(message.chat.id, f"✅ <b>Safar vaqti muvaffaqiyatli o'zgartirildi: {new_dur}</b>", reply_markup=get_admin_keyboard())

    # 2. Edit Coupon Discount Amount Flow
    elif step == "edit_coupon_amt_input":
        try:
            new_amount = int(message.text.replace(" ", ""))
            coupon_id = state["coupon_id"]
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE coupons SET discount_amount = ? WHERE id = ?", (new_amount, coupon_id))
            conn.commit()
            conn.close()
            del admin_states[message.from_user.id]
            bot.send_message(message.chat.id, f"✅ <b>Kupon chegirmasi {new_amount:,} so'm ga muvaffaqiyatli o'zgartirildi!</b>", reply_markup=get_admin_keyboard())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Iltimos faqat raqam kiriting (masalan: 30000):")

    # 3. New Coupon Flow
    elif step == "coupon_code":
        code = message.text.strip().upper()
        state["code"] = code
        state["step"] = "coupon_amount"
        bot.send_message(message.chat.id, f"Kupon kodi: <code>{code}</code>\n\nEndi chegirma summasini kiriting (so'mda, masalan: <code>20000</code>):")
    elif step == "coupon_amount":
        try:
            amount = int(message.text.replace(" ", ""))
            state["amount"] = amount
            state["step"] = "coupon_days"
            bot.send_message(message.chat.id, f"Chegirma: <b>{amount:,} so'm</b>\n\nKupon necha kunga amal qilsin? (Kun sonini kiriting, masalan: <code>30</code>):")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Iltimos faqat raqam kiriting (masalan: 20000):")
    elif step == "coupon_days":
        try:
            days = int(message.text.strip())
            expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO coupons (code, discount_amount, expiry_date, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(code) DO UPDATE SET
                    discount_amount = excluded.discount_amount,
                    expiry_date = excluded.expiry_date,
                    is_active = 1
            """, (state["code"], state["amount"], expiry))
            conn.commit()
            conn.close()
            del admin_states[message.from_user.id]
            bot.send_message(
                message.chat.id,
                f"✅ <b>Kupon muvaffaqiyatli yaratildi!</b>\n\n"
                f"🏷 Kod: <code>{state['code']}</code>\n"
                f"💰 Chegirma: <b>{state['amount']:,} so'm</b>\n"
                f"⏳ Amal qilish muddati: <b>{days} kun</b> ({expiry})\n\n"
                f"<i>Foydalanuvchilar buyurtma berishda ushbu kuponni kiritsalar avtomatik chegirma oladilar.</i>",
                reply_markup=get_admin_keyboard()
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"Xatolik: {e}")
            del admin_states[message.from_user.id]

    # 4. New News Flow
    elif step == "news_title":
        state["title"] = message.text.strip()
        state["step"] = "news_sub"
        bot.send_message(message.chat.id, "Yangilik tavsifi / qisqa matnini kiriting:")
    elif step == "news_sub":
        state["sub"] = message.text.strip()
        state["step"] = "news_img"
        bot.send_message(
            message.chat.id,
            "📸 <b>Yangilik uchun rasm yuboring:</b>\n\n"
            "• To'g'ridan-to'g'ri rasm faylini yuborishingiz mumkin\n"
            "• Yoki rasm havolasini (URL) yozing\n"
            "• Yoki rasm kerak bo'lmasa <code>yoq</code> deb yozing"
        )
    elif step == "news_img":
        img = message.text.strip()
        if img.lower() in ["yoq", "yo'q", "no", "none"]:
            img = "https://images.unsplash.com/photo-1549924231-f129b911e442?w=800&auto=format&fit=crop&q=80"
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO news (title, subtitle, badge, image_url, created_at, is_active)
            VALUES (?, ?, 'YANGI', ?, ?, 1)
        """, (state["title"], state["sub"], img, created_at))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]
        bot.send_message(
            message.chat.id,
            f"✅ <b>Yangilik ilovaga joylandi!</b>\n\n"
            f"📰 Sarlavha: {state['title']}\n"
            f"📝 Tavsif: {state['sub']}",
            reply_markup=get_admin_keyboard()
        )

    # 5. New Route Flow
    elif step == "route_from":
        state["from"] = message.text.strip()
        state["step"] = "route_to"
        bot.send_message(message.chat.id, "Qayerga (borish manzili, masalan: Samarqand):")
    elif step == "route_to":
        state["to"] = message.text.strip()
        state["step"] = "route_p_standart"
        bot.send_message(message.chat.id, "Standart tarif narxini kiriting (so'mda, masalan: 100000):")
    elif step == "route_p_standart":
        try:
            state["p_standart"] = int(message.text.replace(" ", ""))
            state["step"] = "route_p_camfort"
            bot.send_message(message.chat.id, "Camfort tarif narxini kiriting (so'mda, masalan: 130000):")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Faqat raqam kiriting:")
    elif step == "route_p_camfort":
        try:
            state["p_camfort"] = int(message.text.replace(" ", ""))
            state["step"] = "route_p_biznes"
            bot.send_message(message.chat.id, "Biznes tarif narxini kiriting (so'mda, masalan: 180000):")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Faqat raqam kiriting:")
    elif step == "route_p_biznes":
        try:
            state["p_biznes"] = int(message.text.replace(" ", ""))
            state["step"] = "route_duration"
            bot.send_message(
                message.chat.id,
                "⏱ <b>Safar qancha vaqt davom etadi?</b>\n(Masalan: <code>4 soat</code> yoki <code>3.5 soat</code>):"
            )
        except ValueError:
            bot.send_message(message.chat.id, "❌ Faqat raqam kiriting:")
    elif step == "route_duration":
        duration = message.text.strip()
        title = f"{state['from']} — {state['to']}"
        conn = get_db()
        cursor = conn.cursor()
        category = "TOSHKENTDAN VODIYGA" if "toshkent" in state["from"].lower() else "VODIYDAN TOSHKENTGA"
        default_img = ""
        cursor.execute("""
            INSERT INTO routes (from_city, to_city, title, price_standart, price_camfort, price_biznes, category, image_url, duration_hours, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (state["from"], state["to"], title, state["p_standart"], state["p_camfort"], state["p_biznes"], category, default_img, duration))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]
        bot.send_message(
            message.chat.id,
            f"✅ <b>Yangi yo'nalish muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📍 <b>{title}</b>\n"
            f"⏱ Safar vaqti: <b>{duration}</b>\n"
            f"• Standart: <b>{state['p_standart']:,} so'm</b>\n"
            f"• Camfort: <b>{state['p_camfort']:,} so'm</b>\n"
            f"• Biznes: <b>{state['p_biznes']:,} so'm</b>\n\n"
            f"<i>Ushbu yo'nalish darhol mobil ilovada yo'lovchilarga ko'rinadi.</i>",
            reply_markup=get_admin_keyboard()
        )

    # 6. Reply to Support Ticket
    elif step == "reply_ticket":
        ticket_id = state["ticket_id"]
        reply_text = message.text.strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE support_tickets SET reply = ?, status = 'closed' WHERE id = ?", (reply_text, ticket_id))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]
        bot.send_message(message.chat.id, f"✅ Murojaat #{ticket_id} ga javob muvaffaqiyatli saqlandi!", reply_markup=get_admin_keyboard())

    # 7. New Driver Flow
    elif step == "driver_name":
        state["name"] = message.text.strip()
        state["step"] = "driver_phone"
        bot.send_message(message.chat.id, "Haydovchi telefon raqamini kiriting (masalan: <code>+998901234567</code>):")
    elif step == "driver_phone":
        state["phone"] = message.text.strip()
        state["step"] = "driver_car"
        bot.send_message(message.chat.id, "Avtomobil rusumi va yilini kiriting (masalan: <code>Chevrolet Cobalt 2024</code>):")
    elif step == "driver_car":
        state["car_model"] = message.text.strip()
        state["step"] = "driver_features"
        bot.send_message(message.chat.id, "Mashina davlat raqami va qulayliklarini kiriting (masalan: <code>40 A 777 AA | Konditsioner, Shinam salon</code>):")
    elif step == "driver_features":
        parts = message.text.strip().split("|")
        state["car_number"] = parts[0].strip() if len(parts) > 1 else ""
        state["features"] = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        state["step"] = "driver_photo"
        bot.send_message(
            message.chat.id,
            "📸 <b>Haydovchi avtomobili rasmini yuboring:</b>\n\n"
            "• Rasm faylini shu yerga tashlang\n"
            "• Yoki rasm havolasini (URL) yozing\n"
            "• Yoki rasm kerak bo'lmasa <code>yoq</code> deb yozing"
        )
    elif step == "driver_photo":
        img = message.text.strip()
        if img.lower() in ["yoq", "yo'q", "no", "none"]:
            img = "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800&auto=format&fit=crop&q=80"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drivers (name, phone, car_model, car_number, rating, trips_count, image_url, car_features, is_active)
            VALUES (?, ?, ?, ?, 5.0, 120, ?, ?, 1)
        """, (state["name"], state["phone"], state["car_model"], state.get("car_number", ""), img, state.get("features", "Konditsioner, Shinam salon")))
        conn.commit()
        conn.close()
        del admin_states[message.from_user.id]
        bot.send_message(
            message.chat.id,
            f"✅ <b>Haydovchi muvaffaqiyatli qo'shildi!</b>\n\n"
            f"👤 Ism: <b>{state['name']}</b>\n"
            f"📞 Tel: <b>{state['phone']}</b>\n"
            f"🚘 Mashina: <b>{state['car_model']}</b>\n\n"
            f"<i>Ushbu haydovchi mobil ilovadagi haydovchilar kartasida darhol paydo bo'ladi.</i>",
            reply_markup=get_admin_keyboard()
        )

# 🔘 INLINE CALLBACK QUERY DISPATCHER
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data
    user_id = call.from_user.id

    # Add new route trigger
    if data == "add_new_route" and user_id == ADMIN_ID:
        admin_states[user_id] = {"step": "route_from"}
        bot.send_message(call.message.chat.id, "Qayerdan (boshlanish manzili, masalan: Toshkent):")
        bot.answer_callback_query(call.id)
        return

    # Add new coupon trigger
    if data == "add_new_coupon" and user_id == ADMIN_ID:
        admin_states[user_id] = {"step": "coupon_code"}
        bot.send_message(call.message.chat.id, "🏷 Yangi kupon kodini kiriting (Masalan: <code>CAMFORT2026</code>):")
        bot.answer_callback_query(call.id)
        return

    # Add new news trigger
    if data == "add_new_news" and user_id == ADMIN_ID:
        admin_states[user_id] = {"step": "news_title"}
        bot.send_message(call.message.chat.id, "📢 Yangilik sarlavhasini kiriting (Masalan: <code>Hafta oxiri 30% chegirma!</code>):")
        bot.answer_callback_query(call.id)
        return

    # Add new driver trigger
    if data == "add_new_driver" and user_id == ADMIN_ID:
        admin_states[user_id] = {"step": "driver_name"}
        bot.send_message(call.message.chat.id, "👤 Haydovchi ism-familiyasini kiriting (Masalan: Sardor Akramov):")
        bot.answer_callback_query(call.id)
        return

    # Delete driver
    if data.startswith("del_drv_") and user_id == ADMIN_ID:
        d_id = int(data.replace("del_drv_", ""))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE drivers SET is_active = 0 WHERE id = ?", (d_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Haydovchi o'chirildi!")
        bot.edit_message_text("🗑 Haydovchi muvaffaqiyatli o'chirildi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    # Delete route
    if data.startswith("del_r_") and user_id == ADMIN_ID:
        r_id = int(data.replace("del_r_", ""))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE routes SET is_active = 0 WHERE id = ?", (r_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Yo'nalish o'chirildi!")
        bot.edit_message_text("🗑 Yo'nalish muvaffaqiyatli o'chirildi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    # Edit route price selection
    if data.startswith("edit_r_") and user_id == ADMIN_ID:
        r_id = int(data.replace("edit_r_", ""))
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("🚗 Standart", callback_data=f"set_rp_{r_id}_price_standart"),
            types.InlineKeyboardButton("🚙 Camfort", callback_data=f"set_rp_{r_id}_price_camfort"),
            types.InlineKeyboardButton("🚘 Biznes", callback_data=f"set_rp_{r_id}_price_biznes")
        )
        bot.edit_message_text(
            "Qaysi tarif narxini o'zgartirmoqchisiz?",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    # Set which route price to input
    if data.startswith("set_rp_") and user_id == ADMIN_ID:
        parts = data.split("_")
        r_id = int(parts[2])
        col = "_".join(parts[3:])
        tariff_name = "Standart" if "standart" in col else ("Camfort" if "camfort" in col else "Biznes")
        admin_states[user_id] = {"step": "edit_route_price_input", "route_id": r_id, "tariff_col": col}
        bot.send_message(call.message.chat.id, f"<b>{tariff_name}</b> tarifi uchun yangi narxni kiriting (so'mda):")
        bot.answer_callback_query(call.id)
        return

    # Edit route duration
    if data.startswith("edit_dur_") and user_id == ADMIN_ID:
        r_id = int(data.replace("edit_dur_", ""))
        admin_states[user_id] = {"step": "edit_route_duration_input", "route_id": r_id}
        bot.send_message(call.message.chat.id, "⏱ Ushbu yo'nalish uchun yangi safar vaqtini kiriting (masalan: <code>4 soat</code> yoki <code>3.5 soat</code>):")
        bot.answer_callback_query(call.id)
        return

    # Delete coupon
    if data.startswith("del_c_") and user_id == ADMIN_ID:
        c_id = int(data.replace("del_c_", ""))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE coupons SET is_active = 0 WHERE id = ?", (c_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Kupon o'chirildi!")
        bot.edit_message_text("🗑 Kupon muvaffaqiyatli o'chirildi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    # Edit coupon amount
    if data.startswith("edit_c_") and user_id == ADMIN_ID:
        c_id = int(data.replace("edit_c_", ""))
        admin_states[user_id] = {"step": "edit_coupon_amt_input", "coupon_id": c_id}
        bot.send_message(call.message.chat.id, "Kupon uchun yangi chegirma summasini kiriting (so'mda, masalan: 30000):")
        bot.answer_callback_query(call.id)
        return

    # Delete news
    if data.startswith("del_n_") and user_id == ADMIN_ID:
        n_id = int(data.replace("del_n_", ""))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE news SET is_active = 0 WHERE id = ?", (n_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Yangilik o'chirildi!")
        bot.edit_message_text("🗑 Yangilik muvaffaqiyatli o'chirildi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    # Delete order
    if data.startswith("del_order_") and user_id == ADMIN_ID:
        order_id = int(data.replace("del_order_", ""))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Buyurtma o'chirildi!")
        bot.edit_message_text("🗑 Buyurtma o'chirildi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    # Reply to support ticket
    if data.startswith("reply_ticket_") and user_id == ADMIN_ID:
        ticket_id = int(data.replace("reply_ticket_", ""))
        admin_states[user_id] = {"step": "reply_ticket", "ticket_id": ticket_id}
        bot.send_message(call.message.chat.id, f"Murojaat #{ticket_id} uchun javob matningizni yozing:")
        bot.answer_callback_query(call.id)
        return

    # Driver clicks "Zakazni ko'rish / Qabul qilish" in group
    if data.startswith("view_"):
        raw_val = data.replace("view_", "").strip()
        conn = get_db()
        cursor = conn.cursor()
        order = None

        if raw_val.isdigit():
            cursor.execute("SELECT * FROM orders WHERE id = ?", (int(raw_val),))
            order = cursor.fetchone()

        if not order:
            cursor.execute("SELECT * FROM orders WHERE order_code = ?", (raw_val,))
            order = cursor.fetchone()

        # Fallback 1: Extract order code from group message text (e.g. #CF3886)
        if not order and call.message and call.message.text:
            import re
            m = re.search(r"#([A-Za-z0-9]+)", call.message.text)
            if m:
                code_from_msg = m.group(1)
                cursor.execute("SELECT * FROM orders WHERE order_code = ?", (code_from_msg,))
                order = cursor.fetchone()

        # Fallback 2: Parse message text and auto-save order into DB if missing
        if not order and call.message and call.message.text:
            try:
                import re
                text = call.message.text
                code_match = re.search(r"#([A-Za-z0-9]+)", text)
                order_code = code_match.group(1) if code_match else f"CF{random.randint(1000, 9999)}"

                route_match = re.search(r"Yo'nalish:\s*(?:👉\s*)?([^\n]+)", text)
                route_title = route_match.group(1).strip() if route_match else "Yo'nalish"

                tariff_match = re.search(r"Tarif turi:\s*([^\n]+)", text)
                tariff = tariff_match.group(1).strip() if tariff_match else "Camfort"

                pax_match = re.search(r"Yo'lovchilar soni:\s*(\d+)", text)
                passengers_count = int(pax_match.group(1)) if pax_match else 1

                seat_match = re.search(r"O'rindiq(?:\s*turi)?:\s*([^\n]+)", text)
                seat_choice = seat_match.group(1).strip() if seat_match else "Ixtiyoriy"

                luggage = 1 if "Ha, baqaj" in text else 0

                price_match = re.search(r"To'lov summasi:\s*([0-9\s,]+)\s*so'm", text)
                final_price = int(re.sub(r"[^\d]", "", price_match.group(1))) if price_match else 100000

                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO orders (
                        order_code, passenger_name, passenger_phone, route_title, tariff,
                        passengers_count, seat_choice, has_luggage, base_price, discount_amount,
                        final_price, status, created_at, group_msg_id
                    ) VALUES (?, 'Yo\'lovchi', '+998901234567', ?, ?, ?, ?, ?, ?, 0, ?, 'pending', ?, ?)
                """, (order_code, route_title, tariff, passengers_count, seat_choice, luggage, final_price, final_price, now_str, call.message.message_id))
                conn.commit()
                new_id = cursor.lastrowid
                cursor.execute("SELECT * FROM orders WHERE id = ?", (new_id,))
                order = cursor.fetchone()
            except Exception as ex:
                print(f"Error auto-creating order: {ex}")

        conn.close()

        if not order:
            bot.answer_callback_query(call.id, "Buyurtma topilmadi!", show_alert=True)
            return

        order_id = order["id"]

        if order["status"] == "accepted":
            driver_info = order["driver_name"] or "Boshqa haydovchi"
            bot.answer_callback_query(call.id, f"⚠️ Bu buyurtma allaqachon {driver_info} tomonidan qabul qilingan!", show_alert=True)
            return

        if order["status"] == "cancelled":
            bot.answer_callback_query(call.id, "⚠️ Bu buyurtma mijoz tomonidan bekor qilingan!", show_alert=True)
            return

        # Prepare driver private view
        has_coords = bool(order["location_lat"] and order["location_lng"])
        loc_str = "Kiritilmagan"
        if has_coords:
            loc_str = f"Aniq GPS koordinatalari mavjud ({order['location_lat']:.4f}, {order['location_lng']:.4f})"
        elif order["location_address"]:
            loc_str = order["location_address"]

        luggage_str = "Ha, baqaj kerak (Yukxona)" if order["has_luggage"] else "Yo'q (Faqat qo'l yuki)"

        private_msg = (
            f"🚖 <b>B U Y U R T M A   T A F S I L O T L A R I</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 <b>Zakaz kodi:</b> #{order['order_code']}\n\n"
            f"👤 <b>Yo'lovchi:</b> <b>{order['passenger_name']}</b>\n\n"
            f"📞 <b>Telefon raqami:</b> <code>{order['passenger_phone']}</code>\n\n"
            f"📍 <b>Yo'nalish:</b>\n   👉 <b>{order['route_title']}</b>\n\n"
            f"🚘 <b>Tarif turi:</b> {order['tariff'].upper()}\n\n"
            f"👥 <b>Yo'lovchilar soni:</b> {order['passengers_count']} kishi\n\n"
            f"💺 <b>O'rindiq turi:</b> {order['seat_choice']}\n\n"
            f"🧳 <b>Yuk holati:</b> {luggage_str}\n\n"
            f"💰 <b>To'lov summasi:</b> <b>{order['final_price']:,} so'm</b>\n\n"
            f"📌 <b>Lokatsiya:</b> {loc_str}\n\n"
            f"🕒 <b>Buyurtma vaqti:</b> {order['created_at']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Buyurtmani qabul qilasizmi?"
        )

        markup = types.InlineKeyboardMarkup(row_width=1)
        if has_coords:
            map_url = f"https://maps.google.com/?q={order['location_lat']},{order['location_lng']}"
            markup.add(
                types.InlineKeyboardButton("📍 Lokatsiyani ochish (Google / Yandex xarita)", url=map_url)
            )

        markup.add(
            types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}"),
            types.InlineKeyboardButton("❌ O'tkazib yuborish", callback_data=f"skip_{order_id}")
        )

        try:
            # If coordinates exist, send a native map pin as well!
            if has_coords:
                try:
                    bot.send_location(call.from_user.id, latitude=order['location_lat'], longitude=order['location_lng'])
                except Exception:
                    pass

            bot.send_message(call.from_user.id, private_msg, reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id, "Buyurtma ma'lumotlari botingizga yuborildi! Tekshiring.", show_alert=False)
        except telebot.apihelper.ApiTelegramException:
            bot.answer_callback_query(
                call.id,
                "Iltimos, avval @camfort_taxi_zakaz_bot ga kirib 'Start' tugmasini bosing!",
                show_alert=True
            )
        return

    # Driver accepts order in private chat
    if data.startswith("accept_"):
        order_id = int(data.replace("accept_", ""))
        driver_user = call.from_user
        driver_name = f"@{driver_user.username}" if driver_user.username else driver_user.first_name

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            bot.answer_callback_query(call.id, "Buyurtma topilmadi!", show_alert=True)
            return

        if order["status"] == "accepted":
            conn.close()
            bot.answer_callback_query(call.id, "⚠️ Kechirasiz, buyurtma allaqachon qabul qilingan!", show_alert=True)
            bot.edit_message_text("⚠️ Ushbu buyurtma boshqa haydovchi tomonidan qabul qilib bo'lingan.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            return

        # Check if driver has a registered phone in drivers table
        cursor.execute("SELECT phone FROM drivers WHERE is_active = 1 AND (name LIKE ? OR phone LIKE ?) LIMIT 1", (f"%{driver_name}%", f"%{driver_name}%"))
        drv_row = cursor.fetchone()
        driver_phone = drv_row["phone"] if drv_row else "+998952871666"

        cursor.execute("""
            UPDATE orders
            SET status = 'accepted', driver_id = ?, driver_name = ?, driver_phone = ?
            WHERE id = ? OR order_code = ?
        """, (driver_user.id, driver_name, driver_phone, order_id, str(order_id)))
        conn.commit()

        # Update Driver Group message
        if order["group_msg_id"]:
            accepted_group_msg = (
                f"✅ <b>B U Y U R T M A   Q A B U L   Q I L I N D I !</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👨‍✈️ <b>Qabul qilgan haydovchi:</b>\n"
                f"   👉 <b>{driver_name}</b>\n\n"
                f"🚕 <b>Zakaz kodi:</b> #{order['order_code']}\n\n"
                f"📍 <b>Yo'nalish:</b>\n"
                f"   👉 <b>{order['route_title']}</b>\n\n"
                f"🚘 <b>Tarif turi:</b> {order['tariff'].upper()} ({order['passengers_count']} kishi)\n\n"
                f"💰 <b>Kelishilgan summa:</b> <b>{order['final_price']:,} so'm</b>\n\n"
                f"🕒 <b>Qabul qilingan vaqt:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔒 <i>Ushbu buyurtma band qilindi va boshqa haydovchilarga berilmaydi.</i>"
            )
            done_markup = types.InlineKeyboardMarkup()
            done_markup.add(types.InlineKeyboardButton("🔒 Qabul qilib bo'lingan", callback_data="already_done"))
            try:
                bot.edit_message_text(
                    chat_id=DRIVER_GROUP_ID,
                    message_id=order["group_msg_id"],
                    text=accepted_group_msg,
                    reply_markup=done_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Error editing group msg: {e}")

        conn.close()

        bot.answer_callback_query(call.id, "Buyurtma muvaffaqiyatli qabul qilindi!", show_alert=True)

        driver_accept_markup = types.InlineKeyboardMarkup(row_width=1)
        if order["location_lat"] and order["location_lng"]:
            map_url = f"https://maps.google.com/?q={order['location_lat']},{order['location_lng']}"
            driver_accept_markup.add(
                types.InlineKeyboardButton("📍 Lokatsiyani ochish (Google / Yandex)", url=map_url)
            )

        bot.edit_message_text(
            f"✅ <b>TABRIKLAYMIZ! BUYURTMA SIZGA BIRIKTIRILDI.</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚕 <b>Zakaz:</b> #{order['order_code']}\n\n"
            f"👤 <b>Mijoz:</b> {order['passenger_name']}\n\n"
            f"📞 <b>Telefon raqami:</b> <code>{order['passenger_phone']}</code>\n\n"
            f"📍 <b>Yo'nalish:</b> {order['route_title']}\n\n"
            f"💰 <b>To'lov summasi:</b> <b>{order['final_price']:,} so'm</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Iltimos, zudlik bilan mijoz bilan bog'lanib, jo'nash vaqtini kelishib oling!</i>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=driver_accept_markup,
            parse_mode="HTML"
        )
        return

    # Driver skips order
    if data.startswith("skip_"):
        bot.answer_callback_query(call.id, "Buyurtma o'tkazib yuborildi.")
        bot.edit_message_text("❌ Buyurtma o'tkazib yuborildi. U guruhda boshqa haydovchilar uchun ochiq qoladi.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    if data == "already_done":
        bot.answer_callback_query(call.id, "Bu buyurtma qabul qilingan!", show_alert=True)
        return

if __name__ == "__main__":
    init_db()
    print("Bot started directly...")
    bot.infinity_polling()
