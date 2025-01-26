import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NINJAS_API_KEY = os.getenv("NINJAS_API_KEY")

for token_name, token in [("BOT_TOKEN", TOKEN), 
                          ("OPENWEATHER_API_KEY", OPENWEATHER_API_KEY), 
                          ("NINJAS_API_KEY", NINJAS_API_KEY)]:
    if not token:
        raise ValueError(f"Переменная окружения {token_name} не установлена!")
