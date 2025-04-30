from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
import reddit_scrapper as scrapper

# Correct service imports
from services.top_mover_service import fetch_top_movers
from services.technical_indicator_service import calculate_technical_indicators
from services.portfolio_service import purchase_asset, fetch_portfolio
from services.trade_recommendation_service import (
    calculate_trade_recommendations,
    fetch_trade_recommendation
)

# Load env vars
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------
# GPT / Reddit Endpoints
# ------------------------------

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        if 'conversation_history' not in session:
            session['conversation_history'] = [{
                "role": "system",
                "content": "You are a financial advisor and stock market expert."
            }]

        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query']
        session['conversation_history'].append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session['conversation_history'],
            temperature=0.7,
            max_tokens=200
        )

        answer = response.choices[0].message.content.strip()
        session['conversation_history'].append({"role": "assistant", "content": answer})
        session.modified = True

        return jsonify({'query': query, 'answer': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch_shorts', methods=['GET'])
def fetch_shorts_data():
    try:
        days = request.args.get('lookback', default=7, type=int)
        result = scrapper.scrape_reddit(days_back=days)
        return jsonify({"data": list(result)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ------------------------------
# Midas AI Trading Endpoints
# ------------------------------

@app.route('/midas/asset/top_movers', methods=['GET'])
def get_top_movers():
    try:
        mover = request.args.get('mover', default='gainers')
        result = fetch_top_movers(mover)
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/midas/asset/get_signal/<asset>/<type>', methods=['GET'])
def get_signal(asset, type):
    try:
        result = calculate_technical_indicators(asset, type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/midas/asset/purchase', methods=['POST'])
def purchase():
    try:
        data = request.get_json()
        ticker = data.get('name')
        shares = data.get('shares')
        price = data.get('price')
        result = purchase_asset(ticker, shares, price)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/midas/asset/get_portfolio', methods=['GET'])
def get_portfolio():
    try:
        result = fetch_portfolio()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/midas/asset/get_trade_recommendation/<ticker>/<entryPrice>')
def get_trade_recommendation(ticker, entryPrice):
    try:
        rec = calculate_trade_recommendations(ticker, float(entryPrice))
        return jsonify(rec), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/midas/asset/fetch_trade_recommendation/<ticker>')
def get_saved_trade_recommendation(ticker):
    try:
        rec = fetch_trade_recommendation(ticker)
        return jsonify(rec), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ------------------------------
# App Runner
# ------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
