from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from models import db, User
from config import Config
from routes import routes
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration settings from the Config class
app.config.from_object(Config)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', False)  # Enable debug mode for dev

# Initialize the database
db.init_app(app)

# Define the Swagger UI documentation URL and the file location
SWAGGER_URL = '/apidoc'
API_URL = '/static/supplierApiSchema.json'

# Setup Swagger UI with the defined settings
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Supplier Management API" 
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Define a simple route for the home page
@app.route('/', methods=['GET'])
def index():
    return "Supplier Risk Check API"

# Handle ValueError exceptions globally
@app.errorhandler(ValueError)
def handle_value_error(error):
    return jsonify({'error': str(error)}), 400  

# Handle generic internal server errors
@app.errorhandler(500)
def internal_error(error):
    return "An error occurred!", 500 

# Create database tables and default admin user if not exists
with app.app_context():
    db.create_all()

    # Check if the admin user exists, if not, create it
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        raise ValueError("No ADMIN_PASSWORD set for the admin user.")

    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password=admin_password, role='admin')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")

# Register routes from the routes blueprint
app.register_blueprint(routes)

# Run the Flask app on the specified host and port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8002)))
