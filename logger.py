import pandas as pd
import os
from openpyxl import load_workbook

class TradeLogger:
    def __init__(self, filename='bitcoin_trades.xlsx'):
        self.filename = filename
        self.columns = [
            'Strategy', 'Side', 'Entry Time', 'Entry Price', 'Exit Time',
            'Exit Price', 'PnL', 'Leverage', 'Conviction %', 'Exit Reason', 'Balance'
        ]
        self._initialize_excel()

    def _initialize_excel(self):
        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=self.columns)
            df.to_excel(self.filename, index=False)
            print(f"Created new log file: {self.filename}")

    def log_trade(self, trade_result):
        """
        Appends a closed trade to the Excel file.
        """
        new_row = {
            'Strategy': trade_result['strategy'],
            'Side': trade_result['side'],
            'Entry Time': trade_result['entry_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'Entry Price': trade_result['entry_price'],
            'Exit Time': trade_result['exit_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'Exit Price': trade_result['exit_price'],
            'PnL': trade_result['pnl'],
            'Leverage': trade_result['leverage'],
            'Conviction %': trade_result['conviction'],
            'Exit Reason': trade_result['exit_reason'],
            'Balance': trade_result['final_balance']
        }

        df = pd.DataFrame([new_row])

        try:
            with pd.ExcelWriter(self.filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                # Find the next empty row
                try:
                    startrow = writer.book['Sheet1'].max_row
                except:
                    startrow = 0
                df.to_excel(writer, index=False, header=False, startrow=startrow)
            print(f"Logged trade to {self.filename}")
        except Exception as e:
            # Fallback if append fails
            print(f"Error logging to Excel: {e}. Attempting full rewrite.")
            existing_df = pd.read_excel(self.filename)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_excel(self.filename, index=False)

if __name__ == "__main__":
    logger = TradeLogger('test_log.xlsx')
    sample_trade = {
        'strategy': 'Test Strategy',
        'side': 'long',
        'entry_time': pd.Timestamp.now(),
        'entry_price': 60000,
        'exit_time': pd.Timestamp.now(),
        'exit_price': 61000,
        'pnl': 5.0,
        'leverage': 5,
        'conviction': 80,
        'exit_reason': 'Take Profit',
        'final_balance': 105.0
    }
    logger.log_trade(sample_trade)
