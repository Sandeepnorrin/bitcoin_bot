import ccxt
import pandas as pd
import time
from datetime import datetime
import pytz

class DataManager:
    def __init__(self, symbol='BTC/USDT', exchange_id='kraken'):
        self.symbol = symbol
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })
        self.ist = pytz.timezone('Asia/Kolkata')

    def fetch_ohlcv(self, timeframe='15m', limit=100):
        """
        Fetches historical OHLCV data.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching data for {timeframe}: {e}")
            return None

    def get_current_price(self):
        """
        Fetches the current ticker price.
        """
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return None

    def get_ist_now(self):
        """
        Returns the current time in IST.
        """
        return datetime.now(self.ist)

if __name__ == "__main__":
    dm = DataManager()
    price = dm.get_current_price()
    print(f"Current BTC Price: {price}")
    print(f"IST Time: {dm.get_ist_now()}")
    df = dm.fetch_ohlcv('30m', limit=5)
    print("Last 5 30m candles:")
    print(df)
