"""
RationalMarkets Complete API Server
- Twilio phone authentication
- PostgreSQL database persistence
- AI trade analysis with Yahoo Finance
- User portfolios and positions tracking
"""

import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt

# Import our modules
from models_v2 import db, User, Portfolio, Trade, Position
from twilio_auth import twilio_auth
from trade_analyzer import TradeAnalyzer

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://localhost/rationalmarkets'
).replace('postgres://', 'postgresql://')  # Fix for Heroku/Railway
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db.init_app(app)

# Initialize trade analyzer
trade_analyzer = TradeAnalyzer()


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/send-code', methods=['POST'])
def send_verification_code():
    """Send OTP verification code to phone number"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Send verification code via Twilio
    result = twilio_auth.send_verification_code(phone)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': result['message']
        })
    else:
        return jsonify({
            'success': False,
            'error': result['message']
        }), 400


@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code():
    """Verify OTP code and create/login user"""
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    name = data.get('name')  # Optional for new users
    
    if not phone or not code:
        return jsonify({'error': 'Phone and code are required'}), 400
    
    # Verify code with Twilio
    result = twilio_auth.verify_code(phone, code)
    
    if not result['verified']:
        return jsonify({
            'success': False,
            'error': result['message']
        }), 400
    
    # Find or create user
    user = User.query.filter_by(phone=phone).first()
    
    if not user:
        # Create new user
        user = User(
            phone=phone,
            phone_verified=True,
            name=name,
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        
        # Create default portfolio
        portfolio = Portfolio(
            user=user,
            name='My Portfolio',
            currency='USD'
        )
        db.session.add(portfolio)
        db.session.commit()
        
        is_new_user = True
    else:
        # Update existing user
        user.phone_verified = True
        user.last_login = datetime.utcnow()
        if name and not user.name:
            user.name = name
        db.session.commit()
        
        is_new_user = False
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'phone': user.phone,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'isNewUser': is_new_user,
        'token': token,
        'user': user.to_dict()
    })


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info from JWT token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


# ============================================================================
# TRADE ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/analyze-trade', methods=['POST'])
def analyze_trade():
    """AI-powered trade analysis with real market data"""
    # Get user from token (optional - can be anonymous)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = None
    portfolio = None
    
    if token:
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            if user:
                portfolio = Portfolio.query.filter_by(user_id=user.id).first()
        except:
            pass  # Anonymous analysis allowed
    
    data = request.json
    trade_name = data.get('tradeName')
    trade_description = data.get('tradeDescription')
    
    if not trade_name or not trade_description:
        return jsonify({'error': 'Trade name and description are required'}), 400
    
    # Analyze trade with AI
    analysis = trade_analyzer.analyze_trade(trade_name, trade_description)
    
    # Save to database if user is logged in
    if user and portfolio:
        trade = Trade(
            user_id=user.id,
            portfolio_id=portfolio.id,
            trade_name=trade_name,
            trade_description=trade_description,
            recommendation=analysis.get('recommendation'),
            risk_level=analysis.get('riskLevel'),
            ai_rationale=analysis.get('aiRationale'),
            return_estimates=analysis.get('returnEstimates'),
            status='active'
        )
        db.session.add(trade)
        db.session.flush()  # Get trade.id
        
        # Save positions
        for position_data in analysis.get('longs', []) + analysis.get('shorts', []) + analysis.get('derivatives', []):
            position = Position(
                trade_id=trade.id,
                portfolio_id=portfolio.id,
                ticker=position_data.get('ticker'),
                security_name=position_data.get('name'),
                security_type=position_data.get('securityType'),
                position_type=position_data.get('positionType'),
                allocation=float(position_data.get('allocation', '0').replace('%', '')),
                current_price=position_data.get('currentPrice'),
                status='recommended',
                rationale=position_data.get('rationale')
            )
            db.session.add(position)
        
        db.session.commit()
        
        # Add trade ID to response
        analysis['tradeId'] = trade.id
    
    return jsonify(analysis)


@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get user's trade history"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        trades = Trade.query.filter_by(user_id=user.id).order_by(Trade.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'trades': [trade.to_dict() for trade in trades]
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


@app.route('/api/trades/<int:trade_id>', methods=['GET'])
def get_trade(trade_id):
    """Get specific trade details"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        trade = Trade.query.filter_by(id=trade_id, user_id=user.id).first()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        return jsonify({
            'success': True,
            'trade': trade.to_dict()
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get user's portfolio"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        portfolio = Portfolio.query.filter_by(user_id=user.id).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get all positions
        positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
        
        return jsonify({
            'success': True,
            'portfolio': portfolio.to_dict(),
            'positions': [pos.to_dict() for pos in positions]
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RationalMarkets API',
        'database': 'connected' if db.engine else 'disconnected',
        'twilio': 'configured' if not twilio_auth.mock_mode else 'mock_mode'
    })


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.before_first_request
def create_tables():
    """Create database tables"""
    db.create_all()
    print("✅ Database tables created")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    
    print("=" * 80)
    print("RationalMarkets Complete API Server")
    print("=" * 80)
    print(f"Server: http://localhost:{port}")
    print("Features:")
    print("  ✅ Twilio phone authentication")
    print("  ✅ PostgreSQL database persistence")
    print("  ✅ AI trade analysis with Yahoo Finance")
    print("  ✅ User portfolios and positions tracking")
    print("=" * 80)
    print("Endpoints:")
    print("  POST /api/auth/send-code - Send OTP to phone")
    print("  POST /api/auth/verify-code - Verify OTP and login")
    print("  GET  /api/auth/me - Get current user")
    print("  POST /api/analyze-trade - AI trade analysis")
    print("  GET  /api/trades - Get user's trades")
    print("  GET  /api/trades/<id> - Get specific trade")
    print("  GET  /api/portfolio - Get user's portfolio")
    print("  GET  /health - Health check")
    print("=" * 80)
    print("Press Ctrl+C to stop")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=port, debug=False)

