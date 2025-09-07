# simulate_backtest.py

from services.intelligence.strategy_evaluator import StrategyEvaluator

def main():
    evaluator = StrategyEvaluator()
    ticker = "AMC"  # Pick any valid stock
    results = evaluator.run_all_backtests(ticker, days=60)

    print(f"\nBacktest results for {ticker}:\n")
    for res in results:
        print(f"{res['strategy']}: {res['result']}")

if __name__ == "__main__":
    main()
