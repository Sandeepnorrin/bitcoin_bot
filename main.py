import time
import schedule
from data_manager import DataManager
from strategies import Strategies
from trade_engine import TradeEngine
from logger import TradeLogger
import pandas as pd

def main():
    print("Starting Bitcoin Trading Bot...")
    dm = DataManager()
    engine = TradeEngine(initial_balance=100)
    logger = TradeLogger('bitcoin_trades.xlsx')

    # Pre-fetch some data
    print("Fetching initial historical data...")
    timeframes = ['5m', '15m', '30m', '1d', '1w']
    df_map = {}

    for tf in timeframes:
        limit = 210 if tf in ['1d', '1w'] else 100
        df = dm.fetch_ohlcv(tf, limit=limit)
        if df is not None:
            df_map[tf] = df
        else:
            print(f"Warning: Could not fetch initial data for {tf}")

    def update_data():
        nonlocal df_map
        for tf in timeframes:
            limit = 210 if tf in ['1d', '1w'] else 100
            new_df = dm.fetch_ohlcv(tf, limit=limit)
            if new_df is not None:
                df_map[tf] = new_df

    def check_signals():
        nonlocal df_map
        current_time_ist = dm.get_ist_now()
        current_price = dm.get_current_price()
        if not current_price:
            return

        # 1. Update existing trades
        closed_trades = engine.update_trades(current_price, current_time_ist, Strategies, df_map)
        for trade in closed_trades:
            logger.log_trade(trade)
            print(f"CLOSED: {trade['strategy']} | PnL: {trade['pnl']:.2f} | New Balance: {engine.balance:.2f}")

        # 2. Check for new signals if space available
        if engine.can_open_trade():
            signals = []

            # Ensure we have the data needed for each strategy
            if '30m' in df_map:
                s1 = Strategies.strategy_1_12pm_price_action(df_map['30m'], current_time_ist)
                if s1: signals.append(s1)

            if '5m' in df_map:
                s2_5 = Strategies.strategy_2_10ema_trend(df_map['5m'], '5m')
                if s2_5: signals.append(s2_5)

            if '15m' in df_map:
                s2_15 = Strategies.strategy_2_10ema_trend(df_map['15m'], '15m')
                if s2_15: signals.append(s2_15)

                s3 = Strategies.strategy_3_5ema_reversal(df_map['15m'])
                if s3: signals.append(s3)

                s6 = Strategies.strategy_6_sr_zones(df_map['15m'])
                if s6: signals.append(s6)

            if '1d' in df_map:
                s4 = Strategies.strategy_4_200ema_rsi_swing(df_map['1d'])
                if s4: signals.append(s4)

                if '1w' in df_map:
                    s5 = Strategies.strategy_5_slow_stochastic(df_map['1d'], df_map['1w'])
                    if s5: signals.append(s5)

            # Process signals (First come first served)
            for signal in signals:
                if engine.can_open_trade():
                    # Check if already in this strategy
                    if any(t['strategy'] == signal['strategy'] for t in engine.active_trades):
                        continue

                    if engine.open_trade(signal, current_time_ist):
                        print(f"OPENED: {signal['strategy']} {signal['signal']} @ {signal['entry_price']}")
                else:
                    break

    # Schedule data updates and signal checks
    schedule.every(1).minutes.do(update_data)
    schedule.every(1).minutes.do(check_signals)

    # Run once at start
    update_data()
    check_signals()

    print("Bot is running. Press Ctrl+C to stop.")
    last_status = time.time()
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)

            # Status update every 10 mins
            if time.time() - last_status > 600:
                print(f"Status: Balance=${engine.balance:.2f} | Active Trades: {len(engine.active_trades)}")
                last_status = time.time()
        except KeyboardInterrupt:
            print("Stopping bot...")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
