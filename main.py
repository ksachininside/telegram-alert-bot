import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time

# === Configuration ===
SYMBOL = "^NSEI"
EMA_PERIOD = 50
ATR_PERIOD = 10
ATR_MULTIPLIER = 3
INTERVAL = "1h"
LOOKBACK_DAYS = "7d"

# === Telegram Bot ===
BOT_TOKEN = "7863373756:AAE6q89x5ku5ZH2g1IZ789_879FI31Hra_M"
CHAT_ID = "972261464"

# === Send Telegram Message ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        print(response.json())
    except Exception as e:
        print("Telegram error:", e)

# === Supertrend Calculation ===
def supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    df['ATR'] = df['High'].rolling(period).max() - df['Low'].rolling(period).min()
    df['ATR'] = df['ATR'].rolling(period).mean()

    df['UpperBand'] = hl2 + multiplier * df['ATR']
    df['LowerBand'] = hl2 - multiplier * df['ATR']
    df['Supertrend'] = True

    for i in range(period, len(df)):
        if df['Close'][i] > df['UpperBand'][i - 1]:
            df['Supertrend'][i] = True
        elif df['Close'][i] < df['LowerBand'][i - 1]:
            df['Supertrend'][i] = False
        else:
            df['Supertrend'][i] = df['Supertrend'][i - 1]

            if df['Supertrend'][i]:
                df['LowerBand'][i] = max(df['LowerBand'][i], df['LowerBand'][i - 1])
            else:
                df['UpperBand'][i] = min(df['UpperBand'][i], df['UpperBand'][i - 1])
    return df

# === Main Alert Logic ===
def main():
    df = yf.download(SYMBOL, interval=INTERVAL, period=LOOKBACK_DAYS)

    if df.empty or len(df) < 50:
        send_telegram_message("⚠️ Not enough data to calculate indicators.")
        return

    df['EMA'] = df['Close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    df = supertrend(df, ATR_PERIOD, ATR_MULTIPLIER)

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    message = None

    # Example: EMA crossover with Supertrend confirmation
    if previous['Close'] < previous['EMA'] and latest['Close'] > latest['EMA'] and latest['Supertrend']:
        message = "🔔 Buy Signal: EMA crossover + Supertrend confirmation ✅"
    elif previous['Close'] > previous['EMA'] and latest['Close'] < latest['EMA'] and not latest['Supertrend']:
        message = "🔻 Sell Signal: EMA breakdown + Supertrend confirmation ❌"

    if message:
        send_telegram_message(message)
    else:
        print("✅ No signal generated.")

# === Loop (if running continuously) ===
if __name__ == "__main__":
    main()
    # To run every hour automatically on Render, set up a cron job in Render scheduler (optional)
