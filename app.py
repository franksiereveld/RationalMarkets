"""
RationalMarkets API Server with Authentication
AI-powered trade analysis with user authentication and database persistence
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trade_analyzer import analyze_trade_with_ai
from auth import get_auth_service, require_auth, optional_auth
from database import init_database, DatabaseSession
from models import User, Trade, Position, Security, Investment

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database
print("Initializing database...")
db = init_database()
print(f"Database initialized: {db.database_url}")

# Get auth service
auth_service = get_auth_service()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/request-code', methods=['POST'])
def request_verification_code():
    """Request SMS verification code for phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('phoneNumber', '').strip()
        
        if not phone_number:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
        
        result = auth_service.request_verification_code(phone_number)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        print(f"Error requesting verification code: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500


@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code():
    """Verify SMS code and return JWT token"""
    try:
        data = request.get_json()
        phone_number = data.get('phoneNumber', '').strip()
        code = data.get('code', '').strip()
        full_name = data.get('fullName', '').strip() or None
        
        if not phone_number or not code:
            return jsonify({
                'success': False,
                'message': 'Phone number and code are required'
            }), 400
        
        result = auth_service.verify_code(phone_number, code, full_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        print(f"Error verifying code: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user info"""
    return jsonify({
        'success': True,
        'user': request.user
    }), 200


@app.route('/api/auth/test-login', methods=['POST'])
def test_login():
    """TEST ONLY: Create a test user and return JWT token (bypasses Twilio)"""
    try:
        data = request.get_json()
        test_phone = data.get('phoneNumber', '+15551234567')
        
        with DatabaseSession() as session:
            # Get or create test user
            user = session.query(User).filter_by(phone_number=test_phone).first()
            
            if not user:
                user = User(
                    phone_number=test_phone,
                    is_verified=True,
                    last_login=datetime.utcnow(),
                    full_name='Test User'
                )
                session.add(user)
                session.commit()
            else:
                user.last_login = datetime.utcnow()
                session.commit()
            
            # Generate JWT token
            token = auth_service.generate_jwt_token(user)
            
            return jsonify({
                'success': True,
                'message': 'Test login successful',
                'token': token,
                'user': {
                    'id': str(user.id),
                    'phone_number': user.phone_number,
                    'full_name': user.full_name
                }
            }), 200
    
    except Exception as e:
        print(f"Error in test login: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# TRADE ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/analyze-trade', methods=['POST', 'OPTIONS'])
@optional_auth
def analyze_trade():
    """Analyze a trade idea using AI with real market data"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Parse request
        data = request.get_json()
        trade_name = data.get('tradeName', '').strip()
        trade_description = data.get('tradeDescription', '').strip()
        include_derivatives = data.get('includeDerivatives', False)  # Default to False
        
        if not trade_name or not trade_description:
            return jsonify({
                'error': 'Both tradeName and tradeDescription are required'
            }), 400
        
        print(f"\n{'='*80}")
        print(f"Analyzing Trade: {trade_name}")
        if request.user:
            print(f"User: {request.user.get('phoneNumber', 'Unknown')}")
        print(f"Include Derivatives: {include_derivatives}")
        print(f"{'='*80}\n")
        
        # Call AI trade analyzer
        result = analyze_trade_with_ai(trade_name, trade_description, include_derivatives)
        
        # Save to database if user is authenticated
        if request.user:
            try:
                from uuid import UUID
                
                # Convert user_id string to UUID object
                user_id_str = request.user['id']
                if isinstance(user_id_str, str):
                    user_id = UUID(user_id_str)
                else:
                    user_id = user_id_str
                
                with DatabaseSession() as session:
                    # Create trade record
                    trade = Trade(
                        user_id=user_id,
                        trade_name=trade_name,
                        trade_description=trade_description,
                        ai_rationale=result.get('aiRationale'),
                        recommendation=result.get('recommendation'),
                        risk_level=result.get('riskLevel'),
                        analyzed_at=datetime.utcnow()
                    )
                    
                    # Parse return estimates
                    return_estimates = result.get('returnEstimates', {})
                    if return_estimates:
                        trade.return_1m = float(return_estimates.get('1M', '0').rstrip('%')) if return_estimates.get('1M') else None
                        trade.return_3m = float(return_estimates.get('3M', '0').rstrip('%')) if return_estimates.get('3M') else None
                        trade.return_6m = float(return_estimates.get('6M', '0').rstrip('%')) if return_estimates.get('6M') else None
                        trade.return_1y = float(return_estimates.get('1Y', '0').rstrip('%')) if return_estimates.get('1Y') else None
                        trade.return_3y = float(return_estimates.get('3Y', '0').rstrip('%')) if return_estimates.get('3Y') else None
                    
                    session.add(trade)
                    session.flush()  # Get trade.id
                    
                    # Create position records
                    for position_list, position_type in [
                        (result.get('longs', []), 'long'),
                        (result.get('shorts', []), 'short'),
                        (result.get('derivatives', []), 'derivative')
                    ]:
                        for pos_data in position_list:
                            # Get or create security
                            ticker = pos_data.get('ticker')
                            if ticker:
                                security = session.query(Security).filter_by(ticker=ticker).first()
                                if not security:
                                    security = Security(
                                        ticker=ticker,
                                        name=pos_data.get('name', ticker),
                                        security_type=pos_data.get('securityType', 'equity')
                                    )
                                    session.add(security)
                                    session.flush()
                                
                                # Create position
                                allocation_str = pos_data.get('allocation', '0%').rstrip('%')
                                position = Position(
                                    trade_id=trade.id,
                                    security_id=security.id,
                                    position_type=position_type,
                                    security_type=pos_data.get('securityType', 'equity'),
                                    allocation_percent=float(allocation_str) if allocation_str else 0,
                                    rationale=pos_data.get('rationale')
                                )
                                session.add(position)
                    
                    session.commit()
                    result['tradeId'] = str(trade.id)
                    print(f"Trade saved to database: {trade.id}")
            
            except Exception as e:
                print(f"Error saving trade to database: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*80}")
        print(f"Analysis Complete")
        print(f"{'='*80}\n")
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/trades', methods=['GET'])
@require_auth
def get_user_trades():
    """Get all trades for authenticated user"""
    try:
        from sqlalchemy.orm import joinedload
        from uuid import UUID
        
        # Convert user_id string to UUID object
        user_id_str = request.user['id']
        if isinstance(user_id_str, str):
            user_id = UUID(user_id_str)
        else:
            user_id = user_id_str
        
        with DatabaseSession() as session:
            # Eagerly load positions, securities, and user to avoid lazy loading issues
            trades = session.query(Trade).options(
                joinedload(Trade.positions).joinedload(Position.security),
                joinedload(Trade.user)
            ).filter_by(
                user_id=user_id
            ).order_by(Trade.created_at.desc()).all()
            
            # Convert to dict while still in session context
            trades_data = [trade.to_dict() for trade in trades]
        
        return jsonify({
            'success': True,
            'trades': trades_data
        }), 200
    
    except Exception as e:
        print(f"Error getting trades: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to fetch trades: {str(e)}'
        }), 500


@app.route('/api/trades/<trade_id>', methods=['GET'])
@require_auth
def get_trade(trade_id):
    """Get a specific trade by ID"""
    try:
        from sqlalchemy.orm import joinedload
        
        with DatabaseSession() as session:
            trade = session.query(Trade).options(
                joinedload(Trade.positions).joinedload(Position.security),
                joinedload(Trade.user)
            ).filter_by(
                id=trade_id,
                user_id=request.user['id']
            ).first()
            
            if not trade:
                return jsonify({
                    'success': False,
                    'message': 'Trade not found'
                }), 404
            
            trade_data = trade.to_dict()
        
        return jsonify({
            'success': True,
            'trade': trade_data
        }), 200
    
    except Exception as e:
        print(f"Error getting trade: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch trade'
        }), 500


@app.route('/api/trades/<trade_id>', methods=['DELETE'])
@require_auth
def delete_trade(trade_id):
    """Delete a trade"""
    try:
        with DatabaseSession() as session:
            trade = session.query(Trade).filter_by(
                id=trade_id,
                user_id=request.user['id']
            ).first()
            
            if not trade:
                return jsonify({
                    'success': False,
                    'message': 'Trade not found'
                }), 404
            
            session.delete(trade)
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trade deleted successfully'
        }), 200
    
    except Exception as e:
        print(f"Error deleting trade: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete trade'
        }), 500


# ============================================================================
# INVESTMENT ENDPOINTS
# ============================================================================

@app.route('/api/investments', methods=['POST'])
@require_auth
def create_investment():
    """Create a new paper trading investment"""
    try:
        from uuid import UUID
        
        data = request.get_json()
        trade_id = data.get('trade_id')
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        invested_at = data.get('invested_at')  # Optional, defaults to now
        
        if not trade_id or not amount:
            return jsonify({
                'success': False,
                'message': 'Trade ID and amount are required'
            }), 400
        
        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid amount'
            }), 400
        
        # Convert user_id to UUID
        user_id_str = request.user['id']
        if isinstance(user_id_str, str):
            user_id = UUID(user_id_str)
        else:
            user_id = user_id_str
        
        with DatabaseSession() as session:
            # Verify trade exists and belongs to user
            trade = session.query(Trade).filter_by(
                id=trade_id,
                user_id=user_id
            ).first()
            
            if not trade:
                return jsonify({
                    'success': False,
                    'message': 'Trade not found'
                }), 404
            
            # Create investment
            investment = Investment(
                user_id=user_id,
                trade_id=trade_id,
                amount=amount,
                currency=currency,
                invested_at=datetime.fromisoformat(invested_at) if invested_at else datetime.utcnow()
            )
            
            session.add(investment)
            session.commit()
            
            investment_data = investment.to_dict()
        
        return jsonify({
            'success': True,
            'investment': investment_data
        }), 201
    
    except Exception as e:
        print(f"Error creating investment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to create investment: {str(e)}'
        }), 500


@app.route('/api/investments', methods=['GET'])
@require_auth
def get_user_investments():
    """Get all investments for authenticated user"""
    try:
        from sqlalchemy.orm import joinedload
        from uuid import UUID
        
        # Convert user_id to UUID
        user_id_str = request.user['id']
        if isinstance(user_id_str, str):
            user_id = UUID(user_id_str)
        else:
            user_id = user_id_str
        
        with DatabaseSession() as session:
            # Eagerly load trade and positions
            investments = session.query(Investment).options(
                joinedload(Investment.trade).joinedload(Trade.positions).joinedload(Position.security)
            ).filter_by(
                user_id=user_id,
                status='active'
            ).order_by(Investment.invested_at.desc()).all()
            
            # Convert to dict with trade details
            investments_data = []
            for inv in investments:
                inv_dict = inv.to_dict()
                if inv.trade:
                    inv_dict['trade'] = inv.trade.to_dict()
                investments_data.append(inv_dict)
        
        return jsonify({
            'success': True,
            'investments': investments_data
        }), 200
    
    except Exception as e:
        print(f"Error getting investments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to fetch investments: {str(e)}'
        }), 500


@app.route('/api/investments/<investment_id>', methods=['DELETE'])
@require_auth
def close_investment(investment_id):
    """Close an investment (mark as closed)"""
    try:
        with DatabaseSession() as session:
            investment = session.query(Investment).filter_by(
                id=investment_id,
                user_id=request.user['id']
            ).first()
            
            if not investment:
                return jsonify({
                    'success': False,
                    'message': 'Investment not found'
                }), 404
            
            investment.status = 'closed'
            investment.closed_at = datetime.utcnow()
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Investment closed successfully'
        }), 200
    
    except Exception as e:
        print(f"Error closing investment: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to close investment'
        }), 500


# ============================================================================
# USER STATS
# ============================================================================

@app.route('/api/user/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """Get user statistics"""
    try:
        with DatabaseSession() as session:
            # Count total trades
            total_trades = session.query(Trade).filter_by(
                user_id=request.user['id']
            ).count()
            
            # Count saved trades (all trades are saved)
            saved_trades = total_trades
            
            # Count active positions
            active_positions = session.query(Position).join(Trade).filter(
                Trade.user_id == request.user['id']
            ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_trades': total_trades,
                'saved_trades': saved_trades,
                'active_positions': active_positions
            }
        }), 200
    
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch stats'
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    db_healthy = db.health_check()
    
    # Get version from VERSION file (git not available in Railway)
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
        with open(version_file, 'r') as f:
            version = f.read().strip()
    except:
        version = 'unknown'
    
    return jsonify({
        'status': 'healthy' if db_healthy else 'degraded',
        'service': 'RationalMarkets API',
        'version': version,
        'deployed_at': datetime.utcnow().isoformat(),
        'database': 'connected' if db_healthy else 'disconnected',
        'authentication': 'enabled',
        'twilio': 'configured' if auth_service.twilio_client else 'not configured'
    }), 200


# ============================================================================
# FRONTEND ROUTES - Serve HTML files
# ============================================================================

@app.route('/')
def index():
    """Serve the main landing page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'index.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading index.html: {str(e)}", 500

@app.route('/my-trades.html')
def my_trades():
    """Serve the My Trades page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'my-trades.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading my-trades.html: {str(e)}", 500

@app.route('/ai-analysis.html')
def ai_analysis():
    """Serve the AI Analysis page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'ai-analysis.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading ai-analysis.html: {str(e)}", 500

@app.route('/ai-strategy.html')
def ai_strategy():
    """Serve the AI Strategy demo page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'ai-strategy.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading ai-strategy.html: {str(e)}", 500

@app.route('/auth.html')
def auth_page():
    """Serve the authentication page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'auth.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading auth.html: {str(e)}", 500

@app.route('/profile.html')
def profile_page():
    """Serve the profile page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'profile.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading profile.html: {str(e)}", 500

@app.route('/saved-trades.html')
def saved_trades_page():
    """Serve the saved trades page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'saved-trades.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading saved-trades.html: {str(e)}", 500

@app.route('/index.html')
def index_page():
    """Serve the index page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'index.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading index.html: {str(e)}", 500

@app.route('/community-trades.html')
def community_trades_page():
    """Serve the community trades page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'community-trades.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading community-trades.html: {str(e)}", 500

@app.route('/my-positions.html')
def my_positions_page():
    """Serve the my positions page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'my-positions.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading my-positions.html: {str(e)}", 500

@app.route('/broker-selection.html')
def broker_selection_page():
    """Serve the broker selection page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'broker-selection.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading broker-selection.html: {str(e)}", 500

@app.route('/disclaimer.html')
def disclaimer_page():
    """Serve the disclaimer page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'disclaimer.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading disclaimer.html: {str(e)}", 500

@app.route('/demo-trading.html')
def demo_trading_page():
    """Serve the demo trading page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'demo-trading.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading demo-trading.html: {str(e)}", 500

@app.route('/strategy-enhanced.html')
def strategy_enhanced_page():
    """Serve the enhanced strategy page"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'strategy-enhanced.html')
        return send_file(file_path)
    except Exception as e:
        return f"Error loading strategy-enhanced.html: {str(e)}", 500

@app.route('/auth-check.js')
def auth_check_js():
    """Serve the auth check JavaScript"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'auth-check.js')
        return send_file(file_path, mimetype='application/javascript')
    except Exception as e:
        return f"Error loading auth-check.js: {str(e)}", 500

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images)"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'static', path)
        return send_file(file_path)
    except Exception as e:
        return f"Error loading static file: {str(e)}", 404


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    
    print("\n" + "="*80)
    print("RationalMarkets - AI-Powered Trade Analysis with Authentication")
    print("="*80)
    print(f"Server: http://localhost:{port}")
    print()
    print("Frontend:")
    print(f"  GET  / - Landing page")
    print(f"  GET  /auth.html - Login/Signup")
    print(f"  GET  /my-trades.html - Trade analysis interface")
    print(f"  GET  /ai-analysis.html - AI analysis results")
    print()
    print("Authentication API:")
    print(f"  POST /api/auth/request-code - Request SMS verification code")
    print(f"  POST /api/auth/verify-code - Verify code and get JWT token")
    print(f"  GET  /api/auth/me - Get current user (requires auth)")
    print()
    print("Trade API:")
    print(f"  POST /api/analyze-trade - AI trade analysis (saves if authenticated)")
    print(f"  GET  /api/trades - Get user's trades (requires auth)")
    print(f"  GET  /api/trades/<id> - Get specific trade (requires auth)")
    print(f"  DELETE /api/trades/<id> - Delete trade (requires auth)")
    print()
    print(f"  GET  /health - Health check")
    print("="*80)
    print(f"Database: {db.database_url}")
    print(f"Twilio: {'Configured' if auth_service.twilio_client else 'Not configured (dev mode)'}")
    print("="*80)
    print()
    
    app.run(host='0.0.0.0', port=port, debug=True)

