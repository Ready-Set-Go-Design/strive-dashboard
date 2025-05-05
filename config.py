from decouple import config

DATABASE_URL = config("DATABASE_URL")
JWT_SECRET    = config("JWT_SECRET")
