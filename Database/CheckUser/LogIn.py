from flask import Blueprint, request, jsonify
from Database.Base import Database
import logging
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

login_bp = Blueprint('login', __name__)
db = Database()

SUCCESS_USER_ID = int(os.getenv("SUCCESS_USER_ID"))
BCRYPT_ENCODING = os.getenv("BCRYPT_ENCODING")

@login_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    logging.info(f"Received data: {data}")
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logging.error("Username or password not provided")
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        with db.open_database() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, password FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()

            if user:
                user_id, stored_hashed_password = user
                logging.info(f"Stored hashed password: {stored_hashed_password}")

                # Encode the provided password using the specified encoding
                encoded_password = password.encode(BCRYPT_ENCODING)
                logging.info(f"Provided password (encoded): {encoded_password}")

                if bcrypt.checkpw(encoded_password, stored_hashed_password.encode(BCRYPT_ENCODING)):
                    if user_id == SUCCESS_USER_ID:
                        logging.info(f"User {username} logged in successfully")
                        return jsonify({'message': 'Login successful'}), 200
                    else:
                        logging.warning(f"User {username} does not have the required ID")
                        return jsonify({'error': 'User does not have the required ID'}), 403
                else:
                    logging.warning(f"Incorrect password for username: {username}")
                    return jsonify({'error': 'Invalid username or password'}), 401
            else:
                logging.warning(f"Username not found: {username}")
                return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    
# @login_bp.route('/register', methods=['POST'])
# def register():
#     data = request.json
#     username = data.get('username')
#     password = data.get('password')

#     if not username or not password:
#         return jsonify({'error': 'Username and password are required'}), 400

#     hashed_password = bcrypt.hashpw(password.encode(BCRYPT_ENCODING), bcrypt.gensalt())

#     try:
#         with db.open_database() as conn:
#             cursor = conn.cursor()
#             cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
#             conn.commit()
#             return jsonify({'message': 'User registered successfully'}), 201
#     except Exception as e:
#         logging.error(f"Error during registration: {e}")
#         return jsonify({'error': 'Internal server error'}), 500


#data = {'username': 'adminAccount7592', 'password': '@RensukeKunigami7592'}
