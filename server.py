import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import datetime
import random
import string
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import BOT_TOKEN, ADMIN_ID, DRIVER_GROUP_ID, APP_NAME, SERVER_HOST, SERVER_PORT
from database import get_db, init_db

app = Flask(__name__)
CORS(app)

def telegram_api(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Telegram API error ({method}): {e}")
        return {"ok": False, "error": str(e)}

@app.route("/api/info", methods=["GET"])
def get_info():
    return jsonify({
        "status": "success",
        "appName": APP_NAME,
        "shortNumber": "1144",
        "supportPhone": "+998712001144",
        "telegramSupport": "@akramjonov777",
        "version": "1.0.0"
    })

@app.route("/api/routes", methods=["GET"])
def get_routes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routes WHERE is_active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    routes = []
    for r in rows:
        routes.append({
            "id": r["id"],
            "fromCity": r["from_city"],
            "toCity": r["to_city"],
            "title": r["title"],
            "priceStandart": r["price_standart"],
            "priceCamfort": r["price_camfort"],
            "priceBiznes": r["price_biznes"],
            "category": r["category"] if "category" in r.keys() and r["category"] else "VODIYDAN TOSHKENTGA",
            "imageUrl": r["image_url"] if "image_url" in r.keys() else None,
            "durationHours": r["duration_hours"] if "duration_hours" in r.keys() and r["duration_hours"] else "4 soat",
        })
    return jsonify({"status": "success", "routes": routes})

@app.route("/api/drivers", methods=["GET"])
def get_drivers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers WHERE is_active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    drivers = []
    for r in rows:
        drivers.append({
            "id": r["id"],
            "name": r["name"],
            "phone": r["phone"],
            "carModel": r["car_model"],
            "carNumber": r["car_number"] if "car_number" in r.keys() else None,
            "rating": r["rating"] if "rating" in r.keys() else 5.0,
            "tripsCount": r["trips_count"] if "trips_count" in r.keys() else 150,
            "imageUrl": r["image_url"] if "image_url" in r.keys() else None,
            "carFeatures": r["car_features"] if "car_features" in r.keys() else "Konditsioner, Shinam salon",
        })
    return jsonify({"status": "success", "drivers": drivers})

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()

    reviews = []
    for r in rows:
        reviews.append({
            "id": r["id"],
            "userName": r["user_name"],
            "route": r["route"],
            "rating": r["rating"],
            "comment": r["comment"],
            "date": r["date"],
            "orderCode": r["order_code"] if "order_code" in r.keys() else ""
        })
    return jsonify({"status": "success", "reviews": reviews})

@app.route("/api/reviews", methods=["POST"])
def submit_review():
    data = request.json or {}
    user_name = (data.get("userName") or "Yo'lovchi").strip()
    route = (data.get("route") or "").strip()
    rating = float(data.get("rating") or 5.0)
    comment = (data.get("comment") or "").strip()
    order_code = (data.get("orderCode") or "").strip()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if not comment:
        return jsonify({"status": "error", "message": "Fikr matnini kiriting!"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reviews (user_name, route, rating, comment, date, order_code)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_name, route, rating, comment, date_str, order_code))
    conn.commit()
    conn.close()

    # Also notify admin in Telegram
    try:
        telegram_api("sendMessage", {
            "chat_id": ADMIN_ID,
            "text": (
                f"⭐ <b>YANGI YO'LOVCHI FIKRI</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Yo'lovchi:</b> {user_name}\n"
                f"📍 <b>Yo'nalish:</b> {route}\n"
                f"⭐ <b>Baho:</b> {rating} yulduz\n"
                f"💬 <b>Izoh:</b> {comment}\n"
                f"🕒 <b>Vaqt:</b> {date_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            ),
            "parse_mode": "HTML"
        })
    except Exception:
        pass

    return jsonify({"status": "success", "message": "Fikringiz muvaffaqiyatli qabul qilindi! Rahmat!"})

@app.route("/api/news", methods=["GET"])
def get_news():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    news_list = []
    for r in rows:
        news_list.append({
            "id": r["id"],
            "title": r["title"],
            "subtitle": r["subtitle"],
            "badge": r["badge"],
            "imageUrl": r["image_url"],
            "createdAt": r["created_at"]
        })
    return jsonify({"status": "success", "news": news_list})

@app.route("/api/check-coupon", methods=["POST"])
def check_coupon():
    data = request.json or {}
    code = (data.get("code") or "").strip().upper()
    if not code:
        return jsonify({"valid": False, "message": "Kupon kodini kiriting!"})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code,))
    coupon = cursor.fetchone()
    conn.close()

    if not coupon:
        return jsonify({"valid": False, "message": "Bunday kupon kodi topilmadi!"})

    expiry = datetime.datetime.strptime(coupon["expiry_date"], "%Y-%m-%d %H:%M:%S")
    if datetime.datetime.now() > expiry:
        return jsonify({"valid": False, "message": "Kupon muddati eskirgan!"})

    return jsonify({
        "valid": True,
        "code": coupon["code"],
        "discountAmount": coupon["discount_amount"],
        "discount_amount": coupon["discount_amount"],
        "message": f"Kupon muvaffaqiyatli qo'llandi! Chegirma: {coupon['discount_amount']:,} so'm"
    })

@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json or {}
    passenger_name = data.get("passengerName", "Yo'lovchi").strip()
    passenger_phone = data.get("passengerPhone", "").strip()
    route_title = data.get("routeTitle", "Toshkent — Samarqand")
    tariff = data.get("tariff", "Camfort")
    passengers_count = int(data.get("passengersCount", 1))
    seat_choice = data.get("seatChoice", "Ixtiyoriy")
    has_luggage = 1 if data.get("hasLuggage") else 0
    base_price = int(data.get("basePrice", 0))
    discount_amount = int(data.get("discountAmount", 0))
    final_price = int(data.get("finalPrice", base_price - discount_amount))
    if final_price < 0:
        final_price = 0
    location_lat = data.get("locationLat")
    location_lng = data.get("locationLng")
    location_address = data.get("locationAddress", "")
    coupon_code = data.get("couponCode", "")

    if not passenger_phone:
        return jsonify({"status": "error", "message": "Telefon raqami talab qilinadi!"}), 400

    order_code = data.get("orderCode") or f"CF{random.randint(1000, 9999)}"
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (
            order_code, passenger_name, passenger_phone, route_title, tariff,
            passengers_count, seat_choice, has_luggage, base_price, discount_amount,
            final_price, location_lat, location_lng, location_address, coupon_code,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        order_code, passenger_name, passenger_phone, route_title, tariff,
        passengers_count, seat_choice, has_luggage, base_price, discount_amount,
        final_price, location_lat, location_lng, location_address, coupon_code,
        created_at
    ))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Send clean order to Driver Telegram Group (NO GPS coordinates in group!)
    luggage_text = "Ha, baqaj kerak (Yukxona)" if has_luggage else "Yo'q (Faqat qo'l yuki)"
    discount_text = f"\n\n🏷 <b>Chegirma kuponi:</b> -{discount_amount:,} so'm" if discount_amount > 0 else ""

    group_msg = (
        f"🚕 <b>Y A N G I   B U Y U R T M A   #{order_code}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <b>Yo'nalish:</b>\n"
        f"   👉 <b>{route_title}</b>\n\n"
        f"🚘 <b>Tarif turi:</b> {tariff.upper()}\n\n"
        f"👥 <b>Yo'lovchilar soni:</b> {passengers_count} kishi\n\n"
        f"💺 <b>O'rindiq:</b> {seat_choice}\n\n"
        f"🧳 <b>Yuk holati:</b> {luggage_text}\n\n"
        f"💰 <b>To'lov summasi:</b> <b>{final_price:,} so'm</b>{discount_text}\n\n"
        f"🕒 <b>Buyurtma vaqti:</b> {created_at}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 <i>Mijoz telefon raqami va aniq xaritasi faqat qabul qiluvchi haydovchiga beriladi!</i>"
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📋 Zakazni ko'rish / Qabul qilish",
                    "callback_data": f"view_{order_id}"
                }
            ]
        ]
    }

    res = telegram_api("sendMessage", {
        "chat_id": DRIVER_GROUP_ID,
        "text": group_msg,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    })

    if res.get("ok"):
        msg_id = res["result"]["message_id"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET group_msg_id = ? WHERE id = ?", (msg_id, order_id))
        conn.commit()
        conn.close()

    return jsonify({
        "status": "success",
        "message": "Buyurtmangiz muvaffaqiyatli qabul qilindi va haydovchilarga yuborildi!",
        "order": {
            "id": order_id,
            "orderCode": order_code,
            "passengerName": passenger_name,
            "passengerPhone": passenger_phone,
            "routeTitle": route_title,
            "tariff": tariff,
            "passengersCount": passengers_count,
            "seatChoice": seat_choice,
            "hasLuggage": bool(has_luggage),
            "finalPrice": final_price,
            "status": "pending",
            "createdAt": created_at
        }
    })

@app.route("/api/orders", methods=["GET"])
def get_user_orders():
    phone = (request.args.get("phone") or "").strip()
    conn = get_db()
    cursor = conn.cursor()
    if phone:
        clean_digits = ''.join(c for c in phone if c.isdigit())
        last9 = clean_digits[-9:] if len(clean_digits) >= 9 else clean_digits
        cursor.execute("""
            SELECT * FROM orders
            WHERE replace(replace(replace(replace(passenger_phone, '+', ''), ' ', ''), '-', ''), '(', '') LIKE ?
            ORDER BY id DESC
        """, (f"%{last9}",))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "orderCode": r["order_code"],
            "passengerName": r["passenger_name"],
            "passengerPhone": r["passenger_phone"],
            "routeTitle": r["route_title"],
            "tariff": r["tariff"],
            "passengersCount": r["passengers_count"],
            "seatChoice": r["seat_choice"],
            "hasLuggage": bool(r["has_luggage"]),
            "basePrice": r["base_price"],
            "discountAmount": r["discount_amount"],
            "finalPrice": r["final_price"],
            "locationLat": r["location_lat"],
            "locationLng": r["location_lng"],
            "status": r["status"],
            "driverName": r["driver_name"],
            "driverPhone": r["driver_phone"],
            "createdAt": r["created_at"]
        })
    return jsonify({"status": "success", "orders": orders})

@app.route("/api/orders/<path:order_ref>/cancel", methods=["POST"])
def cancel_order(order_ref):
    conn = get_db()
    cursor = conn.cursor()
    if str(order_ref).isdigit():
        cursor.execute("SELECT * FROM orders WHERE id = ? OR order_code = ?", (int(order_ref), str(order_ref)))
    else:
        cursor.execute("SELECT * FROM orders WHERE order_code = ?", (str(order_ref),))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return jsonify({"status": "error", "message": "Buyurtma topilmadi!"}), 404

    if order["status"] == "accepted":
        conn.close()
        return jsonify({"status": "error", "message": "Buyurtma allaqachon haydovchi tomonidan qabul qilingan!"}), 400

    order_id = order["id"]
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    conn.commit()

    # Update group message if exists
    if order["group_msg_id"]:
        telegram_api("editMessageText", {
            "chat_id": DRIVER_GROUP_ID,
            "message_id": order["group_msg_id"],
            "text": f"❌ <b>BUYURTMA BEKOR QILINDI</b>\n#{order['order_code']} yo'lovchi tomonidan bekor qilindi.",
            "parse_mode": "HTML"
        })

    conn.close()
    return jsonify({"status": "success", "message": "Buyurtma bekor qilindi!"})

@app.route("/api/support", methods=["POST"])
def submit_support():
    data = request.json or {}
    name = data.get("name", "Mijoz").strip()
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"status": "error", "message": "Xabar matnini kiriting!"}), 400

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO support_tickets (passenger_name, passenger_phone, message, status, created_at)
        VALUES (?, ?, ?, 'open', ?)
    """, (name, phone, message, created_at))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Send notification to Admin Telegram
    admin_msg = (
        f"📨 <b>YANGI MUROJAAT #{ticket_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Mijoz:</b> {name}\n"
        f"📞 <b>Telefon:</b> {phone}\n"
        f"💬 <b>Xabar:</b> {message}\n"
        f"🕒 <b>Vaqt:</b> {created_at}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    telegram_api("sendMessage", {
        "chat_id": ADMIN_ID,
        "text": admin_msg,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "✍️ Javob yozish", "callback_data": f"reply_ticket_{ticket_id}"}
                ]
            ]
        }
    })

    return jsonify({"status": "success", "message": "Murojaatingiz adminga yetkazildi! Tez orada javob qaytaramiz."})

@app.route("/api/support", methods=["GET"])
def get_user_support():
    phone = (request.args.get("phone") or "").strip()
    conn = get_db()
    cursor = conn.cursor()
    if phone:
        cursor.execute("SELECT * FROM support_tickets WHERE passenger_phone = ? ORDER BY id DESC", (phone,))
    else:
        cursor.execute("SELECT * FROM support_tickets ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    tickets = []
    for r in rows:
        tickets.append({
            "id": r["id"],
            "name": r["passenger_name"],
            "phone": r["passenger_phone"],
            "message": r["message"],
            "reply": r["reply"],
            "status": r["status"],
            "createdAt": r["created_at"]
        })
    return jsonify({"status": "success", "tickets": tickets})

if __name__ == "__main__":
    init_db()
    print(f"Starting {APP_NAME} API Server on {SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
