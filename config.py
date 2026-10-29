import os

BOT_TOKEN = "8714344392:AAHRvs2egUEwofF3AAb20jHQQ8IckF8Vjw8"
ADMIN_ID = 6302873072
ADMIN_USERNAME = "akramjonov777"
DRIVER_GROUP_ID = -1003888459573
APP_NAME = "CAMFORT TAXI 1144"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.environ.get("PORT", 5000))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "camfort_taxi.db"))
