from flask import Flask, request, jsonify, session
from openai import OpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS
import praw
import re
from datetime import datetime, timedelta
import reddit_scrapper as scrapper

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")  # Required for session management

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route('/query', methods=['POST'])
def handle_query():
    try:
        # Ensure conversation history is initialized in the session
        if 'conversation_history' not in session:
            session['conversation_history'] = [
                {
                    "role": "system",
                    "content": "You are a financial advisor and stock market expert with in-depth knowledge about "
                               "trading strategies, market trends, and data analysis. Provide insightful and "
                               "actionable advice based on the user's stock-related queries."
                }
            ]

        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query']

        # Append the user's query to the conversation history
        session['conversation_history'].append({"role": "user", "content": query})

        # Process the query using OpenAI ChatCompletion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session['conversation_history'],
            temperature=0.7,
            max_tokens=200
        )

        # Extract the response text
        # answer = response['choices'][0]['message']['content'].strip()
        answer = response.choices[0].message.content.strip()
        # Append the LLM's response to the conversation history
        session['conversation_history'].append({"role": "assistant", "content": answer})

        # Save session
        session.modified = True

        return jsonify({'query': query, 'answer': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/fetch_shorts', methods=['GET'])
def fetch_shorts_data():
    try:
        days = request.args.get('lookback')

        result = scrapper.scrape_reddit(days_back=days)
        response_data = {
            "data": list(result)
        }
        print(result)
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
