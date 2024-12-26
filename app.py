from flask import Flask, request, jsonify

app = Flask(__name__)


from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Replace this with your actual OpenAI API key
openai.api_key = "your_openai_api_key"

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        # Get the query from the request
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query']

        # Process the query using OpenAI GPT
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=query,
            max_tokens=200,
            temperature=0.7
        )

        # Extract and return the response text
        answer = response.choices[0].text.strip()
        return jsonify({'query': query, 'answer': answer}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

