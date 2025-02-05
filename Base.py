from flask import Flask
from flask_cors import CORS
from Message.receivedMessage import message_bp
from Database.CheckUser.LogIn import login_bp
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set Werkzeug logger to WARNING level to suppress request logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire app

# Register the blueprints
app.register_blueprint(message_bp)
app.register_blueprint(login_bp)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 5000
    logging.info(f"Listening on http://{host}:{port}")
    app.run(host=host, port=port)