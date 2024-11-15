from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import OperationalError
from config import Config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config.from_object(Config)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

@app.route('/')
def index():
    return jsonify({"message": "API en funcionamiento"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)