import requests

BOT_TOKEN = "7863373756:AAFSDz0KLem7tk-Tu02Zy4qPQQBF6gO3AtA"
CHAT_ID = 972261464  # this is a number without quotes

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, data=data)
    print(response.json())

if __name__ == "__main__":
    send_telegram_message("🚀 This is a test alert from Python!")