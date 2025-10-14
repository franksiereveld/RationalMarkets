"""
RationalMarkets - Enhanced Flask Application
With database persistence and Twilio authentication
"""

import os
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, static_folder='.')
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "https://rationalmarkets.com", "https://*.github.io"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rationalmarkets.db')

# Fix for Heroku/Railway PostgreSQL URL
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize JWT
jwt = JWTManager(app)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

from models import db, init_db

# Initialize database
init_db(app)

# ============================================================================
# API ROUTES
# ============================================================================

from api_routes import auth_bp, trades_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(trades_bp)

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return {'error': 'Internal server error'}, 500

# ============================================================================
# JWT ERROR HANDLERS
# ============================================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired tokens"""
    return {
        'error': 'Token has expired',
        'message': 'Please log in again'
    }, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid tokens"""
    return {
        'error': 'Invalid token',
        'message': 'Please log in again'
    }, 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    """Handle missing tokens"""
    return {
        'error': 'Authorization required',
        'message': 'Please log in to access this resource'
    }, 401

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("=" * 60)
    print("RationalMarkets API Server")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[0]}@...")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)

