from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import OperationalError
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

@app.route('/')
def index():
    return jsonify({"message": "API en funcionamiento"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)