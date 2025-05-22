import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# Telegram Bot setup
TELEGRAM_BOT_TOKEN = '7863373756:AAFSDz0KLem7tk-Tu02Zy4qPQQBF6gO3AtA'
CHAT_ID = '972261464'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

# Calculate EMA
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# Calculate ATR for Supertrend
def atr(df, period=10):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

# Calculate Supertrend
def supertrend(df, period=10, multiplier=3):
    atr_value = atr(df, period)
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + (multiplier * atr_value)
    lowerband = hl2 - (multiplier * atr_value)
    
    supertrend = [True] * len(df)  # True = uptrend, False = downtrend
    final_upperband = [0] * len(df)
    final_lowerband = [0] * len(df)
    
    for i in range(1, len(df)):
        final_upperband[i] = upperband[i] if (upperband[i] < final_upperband[i-1] or df['Close'][i-1] > final_upperband[i-1]) else final_upperband[i-1]
        final_lowerband[i] = lowerband[i] if (lowerband[i] > final_lowerband[i-1] or df['Close'][i-1] < final_lowerband[i-1]) else final_lowerband[i-1]

        if supertrend[i-1]:
            supertrend[i] = df['Close'][i] > final_upperband[i]
        else:
            supertrend[i] = df['Close'][i] < final_lowerband[i]
    
    df['Supertrend'] = supertrend
    return df

# Strategy Logic: Supertrend + EMA crossover detection
def check_signals(df):
    signals = []
    for i in range(1, len(df)):
        # Get EMA and Supertrend direction
        ema_current = df['EMA'][i]
        ema_prev = df['EMA'][i-1]
        close_current = df['Close'][i]
        close_prev = df['Close'][i-1]
        supertrend_current = df['Supertrend'][i]

        # Price crosses EMA up/down
        cross_up = close_prev < ema_prev and close_current > ema_current
        cross_down = close_prev > ema_prev and close_current < ema_current

        # Buy condition: Supertrend is uptrend (True) and price crosses EMA up or down
        if supertrend_current and (cross_up or cross_down):
            signals.append((df.index[i], "BUY Signal - Supertrend Up & Price crossed EMA"))

        # Sell condition: Supertrend is downtrend (False) and price crosses EMA up or down
        elif not supertrend_current and (cross_up or cross_down):
            signals.append((df.index[i], "SELL Signal - Supertrend Down & Price crossed EMA"))

    return signals

def main():
    symbol = '^NSEI'  # Nifty 50 index symbol on Yahoo Finance
    period = '1d'      # Daily data, can change to '5m' or '15m' for intraday if available
    atr_period = 10
    atr_multiplier = 3
    ema_length = 9

    # Fetch historical data (last 60 days)
    df = yf.download(symbol, period='60d', interval='1d')

    if df.empty:
        print("No data fetched, try again later")
        return

    df['EMA'] = ema(df['Close'], ema_length)
    df = supertrend(df, period=atr_period, multiplier=atr_multiplier)

    signals = check_signals(df)

    if signals:
        for date, message in signals:
            alert_msg = f"{date.date()} - {message}"
            print(alert_msg)
            send_telegram_message(alert_msg)
    else:
        print("No signals generated.")

if __name__ == "__main__":
    main()
