from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'message': 'AI Editorial Team Backend is running!'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Test backend is working'})

@app.route('/api/test')
def test():
    return jsonify({'test': 'success', 'timestamp': 'now'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    print(f"🚀 Starting test Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
