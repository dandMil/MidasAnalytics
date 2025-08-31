<<<<<<< HEAD
from services.intelligence.agent_planner import AgentPlanner
from utils.ta_helpers import fetch_sample_ohlcv

=======
from utils.mock_data_generator import generate_mock_ohlcv
from services.intelligence.agent_planner import AgentPlanner
>>>>>>> de0b42b63c9f2aabd61a1a94a56e3ee60d71ecd9

def main():
    planner = AgentPlanner()

<<<<<<< HEAD
    # Fetch some mock OHLCV data for simulation
    ticker = "AAPL"
    historical_data = fetch_sample_ohlcv(ticker)

    # Plan the trade using our agent
=======
    # Use mock OHLCV data
    ticker = "MOCK"
    historical_data = generate_mock_ohlcv(100)

>>>>>>> de0b42b63c9f2aabd61a1a94a56e3ee60d71ecd9
    plan = planner.plan_trade(historical_data, ticker)

    print("Generated Trade Plan:")
    print(plan)

<<<<<<< HEAD

=======
>>>>>>> de0b42b63c9f2aabd61a1a94a56e3ee60d71ecd9
if __name__ == "__main__":
    main()
