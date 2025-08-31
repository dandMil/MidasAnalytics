from services.intelligence.agent_planner import AgentPlanner
from utils.ta_helpers import fetch_sample_ohlcv


def main():
    planner = AgentPlanner()

    # Fetch some mock OHLCV data for simulation
    ticker = "AAPL"
    historical_data = fetch_sample_ohlcv(ticker)

    # Plan the trade using our agent
    plan = planner.plan_trade(historical_data, ticker)

    print("Generated Trade Plan:")
    print(plan)


if __name__ == "__main__":
    main()
