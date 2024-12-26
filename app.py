from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/api/llm', methods=['POST'])
def analyze():
    data = request.json
    return None


if __name__ == '__main__':
    app.run(debug=True)
