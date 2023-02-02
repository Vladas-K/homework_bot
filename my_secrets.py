import os

from dotenv import load_dotenv

load_dotenv()

practicum_token = os.getenv('PRACTICUM_TOKEN')
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
print(practicum_token)
print(telegram_token)
print(telegram_chat_id)