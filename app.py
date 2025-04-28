from flask import Flask, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)
@app.route('/query', methods=['POST'])
def handle_query():
    try:
        # Get the query from the request
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query']

        # Process the query using OpenAI ChatCompletion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=200
        )

        answer = response.choices[0].message.content
        return jsonify({'query': query, 'answer': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
