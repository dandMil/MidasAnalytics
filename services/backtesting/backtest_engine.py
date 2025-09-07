# services/backtesting/backtest_engine.py

import pandas as pd

class BacktestEngine:
    def run(self, strategy, data, ticker):
        print(f"[BacktestEngine] Backtesting {strategy.__class__.__name__} on {ticker} with {len(data)} bars")

        df = pd.DataFrame(data)
        required_cols = {'o', 'h', 'l', 'c', 'v'}
        print(f' DF HEAD: {df.head}')
        if not required_cols.issubset(df.columns.str.lower()):
            raise ValueError(f"Missing required OHLCV columns: {required_cols - set(df.columns)}")

        df.columns = df.columns.str.lower()

        # ✅ Convert 't' (timestamp) column to datetime index if present
        if 't' in df.columns:
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('date', inplace=True)

        initial_cash = 10000
        cash = initial_cash
        position = 0
        entry_price = 0
        portfolio_values = []
        trade_log = []

        last_signal = 'hold'
        last_price = None
        last_stop = None
        last_take = None
        last_expected_profit = None
        last_expected_loss = None

        for i in range(20, len(df)):
            sub_df = df.iloc[:i + 1].copy()
            price = df.iloc[i]['c']

            try:
                result = strategy.apply(sub_df, ticker)
                last_signal = result.get('signal', 'hold')
                last_price = result.get('price')
                last_stop = result.get('stop_loss')
                last_take = result.get('take_profit')
                last_expected_profit = result.get('expected_profit')
                last_expected_loss = result.get('expected_loss')
            except Exception as e:
                print(f"[Error] Strategy at index {i}: {e}")
                last_signal = 'hold'

            date_str = str(df.index[i]) if df.index.name else "N/A"

            if last_signal == 'buy' and position == 0:
                position = cash / price
                entry_price = price
                cash = 0
                trade_log.append({
                    "date": date_str,
                    "action": "BUY",
                    "price": round(price, 2),
                    "stop_loss": last_stop,
                    "take_profit": last_take
                })
                print(f"[Trade] BUY at {price:.2f}")

            elif last_signal == 'sell' and position > 0:
                cash = position * price
                trade_log.append({
                    "date": date_str,
                    "action": "SELL",
                    "price": round(price, 2),
                    "stop_loss": last_stop,
                    "take_profit": last_take
                })
                print(f"[Trade] SELL at {price:.2f} (entry was {entry_price:.2f})")
                position = 0
                entry_price = 0

            total_value = cash + (position * price)
            portfolio_values.append(total_value)

        final_value = portfolio_values[-1] if portfolio_values else initial_cash
        total_return = round(final_value - initial_cash, 2)

        return {
            "strategy": strategy.__class__.__name__,
            "ticker": ticker,
            "signal": last_signal,
            "price": last_price,
            "stop_loss": last_stop,
            "take_profit": last_take,
            "expected_profit": last_expected_profit,
            "expected_loss": last_expected_loss,
            "total_return": total_return,
            "log": trade_log
        }
