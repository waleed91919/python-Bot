import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Render!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Discord Webhook URLs
WEBHOOK_URL_DATA = "https://discord.com/api/webhooks/1288178828296065108/2WAROM1BSqljiBOyuKkITpb9_FWwYUa8CD6lUZVY-as5CixuWDFbe9ffRkQ1pqjsgPeq"
WEBHOOK_URL_TRADES = "https://discord.com/api/webhooks/1288182450173775902/DCNYnwfe5keDaCKDIEsCcB5FR8m8l_9wB1loAxSKEG7sIvz3_6hx4brZ-Ha5q4l-S2Ge"

# Handelsparameter
trade_parameters = {
    'BTC_USDT': {'threshold': 2, 'expected_profit': 3.5},
    'ETH_USDT': {'threshold': 3, 'expected_profit': 5.5},
    'SOL_USDT': {'threshold': 3, 'expected_profit': 9},
    'TON_USDT': {'threshold': 4, 'expected_profit': 9},
    'KAS_USDT': {'threshold': 3, 'expected_profit': 5},
    'FLUX_USDT': {'threshold': 3, 'expected_profit': 10},
    'ZBU_USDT': {'threshold': 1, 'expected_profit': 10},
    'BNB_USDT': {'threshold': 3, 'expected_profit': 10}
}

# Funktion zum Abrufen der aktuellen Kerzendaten
def fetch_candle_data(symbol):
    url = f"https://api.gateio.ws/api/v4/spot/candlesticks"
    params = {'currency_pair': symbol, 'interval': '1h', 'limit': 1}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            candle = data[0]
            return {
                'symbol': symbol,
                'last_price': float(candle[2]),  # Schlusskurs
                'open_price': float(candle[5]),  # Eröffnungskurs
                'low_price': float(candle[4]),   # Tiefstkurs
                'high_price': float(candle[3]),  # Höchstkurs
                'change_percentage': (float(candle[2]) - float(candle[4])) / float(candle[4]) * 100
            }
        else:
            print(f"Keine Daten für {symbol} erhalten.")
            return None
    else:
        print(f"Fehler beim Abrufen der Daten für {symbol}: {response.status_code}")
        return None

# Funktion zum Senden der Daten an Discord
def send_to_discord(url, message):
    payload = {
        'content': message
    }
    response = requests.post(url, json=payload)
    if response.status_code == 204:
        print("Erfolgreich gesendet")
    else:
        print(f"Fehler beim Senden an Discord: {response.status_code}")

# Hauptfunktion
def main():
    symbols = list(trade_parameters.keys())
    timezone = pytz.timezone('Europe/Berlin')
    open_trades = 0
    max_trades = 2
    investment = 5.0

    while True:
        now = datetime.now(timezone)
        if now.minute % 10 == 0 or now.minute >= 50:
            for symbol in symbols:
                data = fetch_candle_data(symbol)
                if data:
                    params = trade_parameters[symbol]
                    # Senden der Daten an den Daten-Webhook
                    data_message = (f"Symbol: {data['symbol']}\n"
                                    f"Letzter Preis: {data['last_price']}\n"
                                    f"Tiefster Preis: {data['low_price']}\n"
                                    f"Höchster Preis: {data['high_price']}\n"
                                    f"Prozentuale Änderung: {data['change_percentage']:.2f}%")
                    send_to_discord(WEBHOOK_URL_DATA, data_message)
                    
                    # Überprüfen der Handelsbedingungen
                    if data['last_price'] < data['open_price'] and data['change_percentage'] > params['threshold']:
                        if open_trades < max_trades:
                            profit = investment * (params['expected_profit'] / 100)
                            trade_message = (f"Kauf: {symbol}\n"
                                             f"Letzter Preis: {data['last_price']}\n"
                                             f"Prozentuale Änderung: {data['change_percentage']:.2f}%\n"
                                             f"Erwarteter Gewinn: {profit:.2f} EUR")
                            send_to_discord(WEBHOOK_URL_TRADES, trade_message)
                            open_trades += 1
                        if data['high_price'] >= data['last_price'] * (1 + params['expected_profit'] / 100):
                            open_trades -= 1
                            trade_message = (f"Verkauf: {symbol}\n"
                                             f"Gewinn: {profit:.2f} EUR")
                            send_to_discord(WEBHOOK_URL_TRADES, trade_message)
                    # Daten speichern
                    df = pd.DataFrame([data])
                    datei_name = f"{symbol}.csv"
                    df.to_csv(datei_name, mode='a', header=False, index=False)
            # Warten bis zur nächsten Minute
            time.sleep(60 - datetime.now().second)
        else:
            # Warten bis zur nächsten vollen Minute
            time.sleep(60 - datetime.now().second)

if __name__ == "__main__":
    main()
