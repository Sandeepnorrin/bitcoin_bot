import pandas as pd
from datetime import datetime
import pytz

class TradeEngine:
    def __init__(self, initial_balance=100, max_leverage=5, max_active_trades=2):
        self.balance = initial_balance
        self.max_leverage = max_leverage
        self.max_active_trades = max_active_trades
        self.active_trades = []
        self.trade_history = []
        self.ist = pytz.timezone('Asia/Kolkata')

    def can_open_trade(self):
        return len(self.active_trades) < self.max_active_trades

    def open_trade(self, signal, current_time):
        if not self.can_open_trade():
            return False

        # Position sizing: Using half of capital for each of the 2 trades
        # With 5x leverage, the position size is (Balance / 2) * 5
        allocation = self.balance / (self.max_active_trades - len(self.active_trades))
        # More conservative: divide current balance by remaining slots
        # For simplicity, let's say each trade gets 50% of the CURRENT balance.
        trade_capital = self.balance * 0.5
        position_size_usd = trade_capital * self.max_leverage

        trade = {
            'strategy': signal['strategy'],
            'side': signal['signal'],
            'entry_price': signal['entry_price'],
            'entry_time': current_time,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'conviction': signal['conviction'],
            'leverage': self.max_leverage,
            'capital_used': trade_capital,
            'position_size_usd': position_size_usd,
            'amount_btc': position_size_usd / signal['entry_price'],
            'breakeven_set': False
        }

        self.active_trades.append(trade)
        return True

    def update_trades(self, current_price, current_time_ist, strategies_class, df_map):
        closed_trades = []
        for trade in self.active_trades[:]:
            # Strategy 1 Special Rule: If in profit by 2:00 PM, move SL to cost
            if trade['strategy'] == '12PM_Price_Action' and not trade['breakeven_set']:
                if current_time_ist.hour >= 14:
                    pnl = self.calculate_pnl(trade, current_price)
                    if pnl > 0:
                        trade['stop_loss'] = trade['entry_price']
                        trade['breakeven_set'] = True

            # Check Stop Loss
            if trade['side'] == 'long' and current_price <= trade['stop_loss']:
                closed_trades.append(self.close_trade(trade, trade['stop_loss'], current_time_ist, "Stop Loss"))
            elif trade['side'] == 'short' and current_price >= trade['stop_loss']:
                closed_trades.append(self.close_trade(trade, trade['stop_loss'], current_time_ist, "Stop Loss"))

            # Check Take Profit
            elif trade['take_profit'] and (
                (trade['side'] == 'long' and current_price >= trade['take_profit']) or
                (trade['side'] == 'short' and current_price <= trade['take_profit'])
            ):
                closed_trades.append(self.close_trade(trade, trade['take_profit'], current_time_ist, "Take Profit"))

            # Strategy Specific Exit
            else:
                # Strategy 4: 7-8 days hold rule
                if trade['strategy'] == '200EMA_RSI_Swing':
                    trade_duration = current_time_ist - trade['entry_time'].astimezone(self.ist)
                    if trade_duration.days >= 7:
                        closed_trades.append(self.close_trade(trade, current_price, current_time_ist, "7-day hold period reached"))
                        continue

                tf = '15m' # Default tf for check
                if trade['strategy'] == '200EMA_RSI_Swing': tf = '1d'

                df = df_map.get(tf)
                if df is not None:
                    should_exit, reason = strategies_class.check_exit_condition(trade['strategy'], trade, df)
                    if should_exit:
                        closed_trades.append(self.close_trade(trade, current_price, current_time_ist, reason))

        return closed_trades

    def calculate_pnl(self, trade, exit_price):
        if trade['side'] == 'long':
            return (exit_price - trade['entry_price']) * trade['amount_btc']
        else:
            return (trade['entry_price'] - exit_price) * trade['amount_btc']

    def close_trade(self, trade, exit_price, exit_time, reason):
        pnl = self.calculate_pnl(trade, exit_price)
        self.balance += pnl

        trade_result = {
            **trade,
            'exit_price': exit_price,
            'exit_time': exit_time,
            'pnl': pnl,
            'exit_reason': reason,
            'final_balance': self.balance
        }

        self.trade_history.append(trade_result)
        self.active_trades.remove(trade)
        return trade_result
