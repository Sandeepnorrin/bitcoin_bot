# Bitcoin Trading Bot

This is a Python-based Bitcoin trading bot that implements 6 specific strategies and logs virtual trades to an Excel file.

## Strategies Implemented

1. **12 PM Price Action**: Trades the high/low break of the 12:00-12:30 PM IST candle.
2. **10 EMA Trend Following**: Captures trends using the 10 EMA on 5m or 15m charts.
3. **5 EMA Reversal**: Catches reversals when candles form entirely outside the 5 EMA.
4. **200 EMA + RSI Swing**: A high-probability swing strategy on the Daily chart.
5. **Slow Stochastic Momentum**: Uses momentum "cuts" (90/10) to time entries.
6. **S/R Zones (Price Action 2.0)**: Trades Hammer or Bullish Engulfing patterns at Support/Resistance zones.

## Features

- **Paper Trading**: Operates with a virtual $100 balance.
- **Risk Management**: 5x leverage and a maximum of 2 concurrent trades.
- **Detailed Logging**: All trades are logged to `bitcoin_trades.xlsx` with Entry/Exit prices, PnL, Conviction %, and more.
- **Real-time Data**: Uses Kraken via CCXT for free real-time and historical data.

## Requirements

- Python 3.8+
- Dependencies: `pandas`, `pandas_ta`, `ccxt`, `openpyxl`, `pytz`, `schedule`

## Installation

```bash
pip install -r requirements.txt
```

## Running the Bot

Simply run the main script:

```bash
python main.py
```

The bot will run in a loop, checking for signals every minute.

## Files

- `main.py`: Entry point and execution loop.
- `data_manager.py`: Handles data fetching from Kraken.
- `strategies.py`: Contains the logic for all 6 trading strategies.
- `trade_engine.py`: Manages virtual balance, leverage, and active trades.
- `logger.py`: Handles Excel logging.
