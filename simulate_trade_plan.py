from utils.mock_data_generator import generate_mock_ohlcv
from services.intelligence.agent_planner import AgentPlanner

def main():
    planner = AgentPlanner()

    # Use mock OHLCV data
    ticker = "MOCK"
    historical_data = generate_mock_ohlcv(100)

    plan = planner.plan_trade(historical_data, ticker)

    print("Generated Trade Plan:")
    print(plan)

if __name__ == "__main__":
    main()
