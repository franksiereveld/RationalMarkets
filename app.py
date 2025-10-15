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
from models import User, Trade, Position, Security

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
        
        if not phone_number or not code:
            return jsonify({
                'success': False,
                'message': 'Phone number and code are required'
            }), 400
        
        result = auth_service.verify_code(phone_number, code)
        
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
                with DatabaseSession() as session:
                    # Create trade record
                    trade = Trade(
                        user_id=request.user['id'],
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
        with DatabaseSession() as session:
            trades = session.query(Trade).filter_by(
                user_id=request.user['id']
            ).order_by(Trade.created_at.desc()).all()
            
            trades_data = [trade.to_dict() for trade in trades]
        
        return jsonify({
            'success': True,
            'trades': trades_data
        }), 200
    
    except Exception as e:
        print(f"Error getting trades: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch trades'
        }), 500


@app.route('/api/trades/<trade_id>', methods=['GET'])
@require_auth
def get_trade(trade_id):
    """Get a specific trade by ID"""
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
    
    return jsonify({
        'status': 'healthy' if db_healthy else 'degraded',
        'service': 'RationalMarkets API',
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
    
    app.run(host='0.0.0.0', port=port, debug=False)

