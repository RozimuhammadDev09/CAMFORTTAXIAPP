import sqlite3
import datetime
import os
import shutil
from config import DATABASE_PATH

def get_db():
    dir_path = os.path.dirname(DATABASE_PATH)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    if not os.path.exists(DATABASE_PATH):
        init_seed = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camfort_taxi.db")
        if os.path.exists(init_seed) and os.path.abspath(init_seed) != os.path.abspath(DATABASE_PATH):
            try:
                shutil.copy2(init_seed, DATABASE_PATH)
            except Exception:
                pass
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE,
        passenger_name TEXT NOT NULL,
        passenger_phone TEXT NOT NULL,
        route_title TEXT NOT NULL,
        tariff TEXT NOT NULL,
        passengers_count INTEGER NOT NULL,
        seat_choice TEXT,
        has_luggage INTEGER DEFAULT 0,
        base_price INTEGER NOT NULL,
        discount_amount INTEGER DEFAULT 0,
        final_price INTEGER NOT NULL,
        location_lat REAL,
        location_lng REAL,
        location_address TEXT,
        coupon_code TEXT,
        status TEXT DEFAULT 'pending', -- pending, accepted, rejected, completed, cancelled
        driver_id INTEGER,
        driver_name TEXT,
        driver_phone TEXT,
        group_msg_id INTEGER,
        created_at TEXT NOT NULL
    )
    """)

    # Routes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_city TEXT NOT NULL,
        to_city TEXT NOT NULL,
        title TEXT NOT NULL,
        price_standart INTEGER NOT NULL,
        price_camfort INTEGER NOT NULL,
        price_biznes INTEGER NOT NULL,
        category TEXT DEFAULT 'VODIYDAN TOSHKENTGA', -- VODIYDAN TOSHKENTGA, TOSHKENTDAN VODIYGA
        image_url TEXT,
        duration_hours TEXT DEFAULT '4 soat',
        is_active INTEGER DEFAULT 1
    )
    """)

    # Add columns if routes table already existed without them
    for col, col_type in [
        ("category", "TEXT DEFAULT 'VODIYDAN TOSHKENTGA'"),
        ("image_url", "TEXT"),
        ("duration_hours", "TEXT DEFAULT '4 soat'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE routes ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Coupons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_amount INTEGER NOT NULL,
        expiry_date TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    """)

    # News / promos carousel table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subtitle TEXT,
        badge TEXT DEFAULT 'YANGI',
        image_url TEXT,
        created_at TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Drivers table (Our experienced drivers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        car_model TEXT NOT NULL,
        car_number TEXT,
        rating REAL DEFAULT 5.0,
        trips_count INTEGER DEFAULT 150,
        image_url TEXT,
        car_features TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Support appeals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_name TEXT NOT NULL,
        passenger_phone TEXT NOT NULL,
        message TEXT NOT NULL,
        reply TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT NOT NULL
    )
    """)

    # Passenger Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        route TEXT NOT NULL,
        rating REAL DEFAULT 5.0,
        comment TEXT NOT NULL,
        date TEXT NOT NULL,
        order_code TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
