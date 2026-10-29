# CAMFORT TAXI 1144 - Backend & Telegram Bot

Ushbu repozitoriy **CAMFORT TAXI** ilovasi uchun markaziy REST API serveri va dispetcher Telegram botini o'z ichiga oladi.

## Xususiyatlari
- **Flask REST API**: Mobil ilovadan buyurtmalar qabul qilish, narxlar va tariflar ma'lumotlarini yetkazish.
- **Telegram Bot (@camfort_taxi_zakaz_bot)**: Haydovchilar guruhi va mijozlar bilan aloqa, buyurtmalarni taqsimlash.
- **SQLite Database**: Buyurtmalar, tariflar, kuponlar va haydovchilar bazasi.
- **Birlashtirilgan ishga tushirish**: `run_all.py` orqali Flask va Telegram Bot parallel rejimda bitta konteynerda ishlaydi.

## Ishga tushirish (Railway)
- Entry point: `Procfile` (`web: python run_all.py`)
- Port: Railway tomonidan taqdim etiladigan `$PORT` muhit o'zgaruvchisi orqali avtomatik aniqlanadi.
