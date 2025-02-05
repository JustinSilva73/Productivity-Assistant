from flask import Blueprint, request, jsonify
from OpenAI.Assistant import JarvisAssistant
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

jarvis = JarvisAssistant()
message_bp = Blueprint('message', __name__)

@message_bp.route('/askJarvis', methods=['POST'])
def receive_message():
    data = request.json
    message = data.get('message')
    if message:
        logging.info(f"Received message: {message}")
        # Process the message using JarvisAssistant
        try:
            response = jarvis.get_response(message)
            logging.info(f"Sending response: {response}")
            return jsonify({'response': response})
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return jsonify({'error': 'Error processing message'}), 500
    else:
        logging.error("No message provided")
        return jsonify({'error': 'No message provided'}), 400