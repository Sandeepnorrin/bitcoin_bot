from data_manager import DataManager
from strategies import Strategies
import pandas as pd

def check_current_status():
    dm = DataManager()
    ist_now = dm.get_ist_now()
    price = dm.get_current_price()

    print(f"Current BTC Price: {price}")
    print(f"IST Time: {ist_now}")

    df_map = {
        '5m': dm.fetch_ohlcv('5m', limit=100),
        '15m': dm.fetch_ohlcv('15m', limit=100),
        '30m': dm.fetch_ohlcv('30m', limit=100),
        '1d': dm.fetch_ohlcv('1d', limit=210),
        '1w': dm.fetch_ohlcv('1w', limit=60)
    }

    signals = []
    s1 = Strategies.strategy_1_12pm_price_action(df_map['30m'], ist_now)
    if s1: signals.append(s1)
    s2_5 = Strategies.strategy_2_10ema_trend(df_map['5m'], '5m')
    if s2_5: signals.append(s2_5)
    s2_15 = Strategies.strategy_2_10ema_trend(df_map['15m'], '15m')
    if s2_15: signals.append(s2_15)
    s3 = Strategies.strategy_3_5ema_reversal(df_map['15m'])
    if s3: signals.append(s3)
    s4 = Strategies.strategy_4_200ema_rsi_swing(df_map['1d'])
    if s4: signals.append(s4)
    s5 = Strategies.strategy_5_slow_stochastic(df_map['1d'], df_map['1w'])
    if s5: signals.append(s5)
    s6 = Strategies.strategy_6_sr_zones(df_map['15m'])
    if s6: signals.append(s6)

    print("\nPotential/Active Signals:")
    for s in signals:
        rr = abs(s['take_profit'] - s['entry_price']) / abs(s['entry_price'] - s['stop_loss']) if s['take_profit'] else "Dynamic"
        print(f"Strategy: {s['strategy']}")
        print(f"  Side: {s['signal']}")
        print(f"  Entry: {s['entry_price']}")
        print(f"  SL: {s['stop_loss']}")
        print(f"  TP: {s['take_profit']}")
        print(f"  RR Ratio: {rr}")
        print(f"  Conviction: {s['conviction']}%")
        print("-" * 20)

if __name__ == "__main__":
    check_current_status()
