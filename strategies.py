import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategies:
    @staticmethod
    def strategy_1_12pm_price_action(df_30m, current_time_ist):
        """
        1. 12 PM Bitcoin-Specific Price Action (30m chart)
        """
        df = df_30m.copy()
        if df['timestamp'].dt.tz is None:
            df['ist_time'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        else:
            df['ist_time'] = df['timestamp'].dt.tz_convert('Asia/Kolkata')

        target_date = current_time_ist.date()
        candle_12pm = df[(df['ist_time'].dt.date == target_date) &
                         (df['ist_time'].dt.hour == 12) &
                         (df['ist_time'].dt.minute == 0)]

        if candle_12pm.empty:
            return None

        trigger_candle = candle_12pm.iloc[0]
        high = trigger_candle['high']
        low = trigger_candle['low']

        # Latest price from the most recent candle or provided ticker
        last_candle = df.iloc[-1]
        close = last_candle['close']

        # Check if current time is after 12:30 PM IST (when the 12:00 candle closes)
        if current_time_ist.hour < 12 or (current_time_ist.hour == 12 and current_time_ist.minute < 30):
            return None

        signal = None
        entry_price = 0
        sl = 0
        tp = 0
        conviction = 70

        if close > high:
            signal = 'long'
            entry_price = close
            sl = low
            tp = entry_price + (entry_price - sl) * 3
        elif close < low:
            signal = 'short'
            entry_price = close
            sl = high
            tp = entry_price - (sl - entry_price) * 3

        if signal:
            return {
                'strategy': '12PM_Price_Action',
                'signal': signal,
                'entry_price': entry_price,
                'stop_loss': sl,
                'take_profit': tp,
                'conviction': conviction
            }
        return None

    @staticmethod
    def strategy_2_10ema_trend(df, timeframe='15m'):
        """
        2. 10 EMA Bitcoin Trend Following
        """
        df = df.copy()
        df['ema10'] = ta.ema(df['close'], length=10)

        if len(df) < 2 or df['ema10'].isna().iloc[-1]: return None

        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        # Long
        if prev_candle['close'] < prev_candle['open'] and prev_candle['low'] > prev_candle['ema10']:
            if last_candle['close'] > prev_candle['high']:
                return {
                    'strategy': f'10EMA_Trend_{timeframe}',
                    'signal': 'long',
                    'entry_price': last_candle['close'],
                    'stop_loss': prev_candle['low'],
                    'take_profit': last_candle['close'] * 1.1, # Target 1:10ish or trailing
                    'conviction': 75
                }

        # Short
        if prev_candle['close'] > prev_candle['open'] and prev_candle['high'] < prev_candle['ema10']:
            if last_candle['close'] < prev_candle['low']:
                return {
                    'strategy': f'10EMA_Trend_{timeframe}',
                    'signal': 'short',
                    'entry_price': last_candle['close'],
                    'stop_loss': prev_candle['high'],
                    'take_profit': last_candle['close'] * 0.9,
                    'conviction': 75
                }
        return None

    @staticmethod
    def strategy_3_5ema_reversal(df_15m):
        """
        3. 5 EMA Bitcoin Reversal Strategy (15m)
        """
        df = df_15m.copy()
        df['ema5'] = ta.ema(df['close'], length=5)

        if len(df) < 2 or df['ema5'].isna().iloc[-1]: return None

        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        if prev_candle['high'] < prev_candle['ema5'] and last_candle['close'] > prev_candle['high']:
            return {
                'strategy': '5EMA_Reversal',
                'signal': 'long',
                'entry_price': last_candle['close'],
                'stop_loss': prev_candle['low'],
                'take_profit': last_candle['close'] * 1.05,
                'conviction': 80
            }

        if prev_candle['low'] > prev_candle['ema5'] and last_candle['close'] < prev_candle['low']:
            return {
                'strategy': '5EMA_Reversal',
                'signal': 'short',
                'entry_price': last_candle['close'],
                'stop_loss': prev_candle['high'],
                'take_profit': last_candle['close'] * 0.95,
                'conviction': 80
            }
        return None

    @staticmethod
    def strategy_4_200ema_rsi_swing(df_daily):
        """
        4. 200 EMA + RSI Bitcoin Swing Strategy (Daily)
        """
        df = df_daily.copy()
        df['ema200'] = ta.ema(df['close'], length=200)
        df['rsi10'] = ta.rsi(df['close'], length=10)

        if len(df) < 2 or df['ema200'].isna().iloc[-1] or df['rsi10'].isna().iloc[-1]: return None

        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        if last_candle['close'] > last_candle['ema200'] and last_candle['rsi10'] < 35:
            return {
                'strategy': '200EMA_RSI_Swing',
                'signal': 'long',
                'entry_price': last_candle['close'],
                'stop_loss': prev_candle['low'] * 0.995,
                'take_profit': last_candle['close'] * 1.2,
                'conviction': 85
            }
        return None

    @staticmethod
    def strategy_5_slow_stochastic(df_daily, df_weekly):
        """
        5. Slow Stochastic Bitcoin Momentum (Daily)
        """
        df = df_daily.copy()
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
        if stoch is None: return None
        df = pd.concat([df, stoch], axis=1)
        k_col = 'STOCHk_14_3_3'

        df_weekly = df_weekly.copy()
        df_weekly['ema50'] = ta.ema(df_weekly['close'], length=50)

        if len(df) < 2 or len(df_weekly) < 1 or k_col not in df.columns: return None
        if df[k_col].isna().iloc[-1] or df_weekly['ema50'].isna().iloc[-1]: return None

        last_k = df.iloc[-1][k_col]
        prev_k = df.iloc[-2][k_col]
        weekly_close = df_weekly.iloc[-1]['close']
        weekly_ema50 = df_weekly.iloc[-1]['ema50']

        if prev_k < 10 and last_k >= 10 and weekly_close > weekly_ema50:
            entry_price = df.iloc[-1]['close']
            stop_loss = df.iloc[-1]['low'] * 0.98
            take_profit = entry_price + (entry_price - stop_loss) * 3 # 1:3 RR
            return {
                'strategy': 'Slow_Stochastic_Momentum',
                'signal': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'conviction': 65
            }

        if prev_k > 90 and last_k <= 90:
            entry_price = df.iloc[-1]['close']
            stop_loss = df.iloc[-1]['high'] * 1.02
            take_profit = entry_price - (stop_loss - entry_price) * 3 # 1:3 RR
            return {
                'strategy': 'Slow_Stochastic_Momentum',
                'signal': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'conviction': 65
            }
        return None

    @staticmethod
    def strategy_6_sr_zones(df):
        """
        6. Bitcoin Price Action 2.0 (S/R Zones)
        """
        if len(df) < 20: return None

        # Simple S/R detection
        def get_sr_levels(df):
            levels = []
            for i in range(2, len(df) - 2):
                if df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i+1] and \
                   df['low'][i+1] < df['low'][i+2] and df['low'][i-1] < df['low'][i-2]:
                    levels.append(('support', df['low'][i]))
                if df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i+1] and \
                   df['high'][i+1] > df['high'][i+2] and df['high'][i-1] > df['high'][i-2]:
                    levels.append(('resistance', df['high'][i]))
            return levels

        levels = get_sr_levels(df)
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        supports = [l[1] for l in levels if l[0] == 'support' and l[1] < last_candle['close']]
        if not supports: return None

        nearest_support = max(supports)

        # Hammer at support
        is_hammer = (last_candle['high'] - last_candle['low']) > 3 * abs(last_candle['open'] - last_candle['close']) and \
                    (last_candle['close'] - last_candle['low']) > 0.6 * (last_candle['high'] - last_candle['low'])

        # Bullish Engulfing
        is_bullish_engulfing = last_candle['close'] > prev_candle['open'] and \
                               last_candle['open'] < prev_candle['close'] and \
                               prev_candle['close'] < prev_candle['open']

        if last_candle['low'] <= nearest_support * 1.005 and (is_hammer or is_bullish_engulfing):
            entry_price = last_candle['close']
            stop_loss = last_candle['low'] * 0.998
            take_profit = entry_price + (entry_price - stop_loss) * 3 # Aim for at least 1:3 RR
            return {
                'strategy': 'SR_Zones_PriceAction',
                'signal': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'conviction': 90
            }
        return None

    @staticmethod
    def check_exit_condition(strategy_name, position, df_current, df_extra=None):
        """
        Checks if a position should be closed based on strategy-specific exit rules.
        """
        last_candle = df_current.iloc[-1]

        if strategy_name.startswith('10EMA_Trend'):
            ema10 = ta.ema(df_current['close'], length=10).iloc[-1]
            if position['side'] == 'long' and last_candle['close'] < ema10:
                return True, "Price closed below 10 EMA"
            if position['side'] == 'short' and last_candle['close'] > ema10:
                return True, "Price closed above 10 EMA"

        if strategy_name == '5EMA_Reversal':
            ema20 = ta.ema(df_current['close'], length=20).iloc[-1]
            if position['side'] == 'long' and last_candle['close'] < ema20:
                return True, "Price closed below 20 EMA"
            if position['side'] == 'short' and last_candle['close'] > ema20:
                return True, "Price closed above 20 EMA"

        if strategy_name == '200EMA_RSI_Swing':
            rsi10 = ta.rsi(df_current['close'], length=10).iloc[-1]
            if rsi10 > 45:
                return True, "RSI 10 rose above 45"
            # 7-8 days hold check should be in trade engine

        return False, None
