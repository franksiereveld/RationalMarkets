"""
API routes for authentication and trade management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth_service import auth_service
from models import (
    db, get_or_create_user, get_user_by_phone, get_user_trades,
    get_trade_by_id, create_trade, create_position, delete_trade
)

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
trades_bp = Blueprint('trades', __name__, url_prefix='/api/trades')


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@auth_bp.route('/send-code', methods=['POST'])
def send_verification_code():
    """Send OTP verification code to phone number"""
    data = request.get_json()
    phone_number = data.get('phoneNumber')
    
    # Validate phone number
    is_valid, error_message = auth_service.validate_phone_number(phone_number)
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Send verification code
    result = auth_service.send_verification_code(phone_number)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """Verify OTP code and create session"""
    data = request.get_json()
    phone_number = data.get('phoneNumber')
    code = data.get('code')
    
    if not phone_number or not code:
        return jsonify({'error': 'Phone number and code are required'}), 400
    
    # Verify code
    result = auth_service.verify_code(phone_number, code)
    
    if result['success'] and result.get('verified'):
        # Create or get user in database
        user = get_or_create_user(phone_number)
        
        # Add user info to response
        result['user'] = user.to_dict()
        
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'authenticated': True
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should delete token)"""
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Get authentication service status"""
    return jsonify({
        'enabled': auth_service.is_enabled(),
        'devMode': not auth_service.is_enabled(),
        'message': 'Authentication service is ' + ('enabled' if auth_service.is_enabled() else 'in development mode')
    }), 200


# ============================================================================
# TRADE MANAGEMENT ROUTES
# ============================================================================

@trades_bp.route('/', methods=['GET'])
@jwt_required()
def get_trades():
    """Get all trades for current user"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get pagination parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Get trades
    trades = get_user_trades(user.id, limit=limit, offset=offset)
    
    return jsonify({
        'trades': [trade.to_dict() for trade in trades],
        'count': len(trades),
        'limit': limit,
        'offset': offset
    }), 200


@trades_bp.route('/<int:trade_id>', methods=['GET'])
@jwt_required()
def get_trade(trade_id):
    """Get a specific trade"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    trade = get_trade_by_id(trade_id, user.id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    return jsonify({'trade': trade.to_dict()}), 200


@trades_bp.route('/', methods=['POST'])
@jwt_required()
def create_new_trade():
    """Create a new trade with positions"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Trade name is required'}), 400
    
    try:
        # Create trade
        trade = create_trade(
            user_id=user.id,
            name=data.get('name'),
            description=data.get('description', ''),
            recommendation=data.get('recommendation', 'NEUTRAL'),
            risk_level=data.get('riskLevel', 'MODERATE'),
            analysis_text=data.get('analysisText', '')
        )
        
        # Create long positions
        for pos_data in data.get('longPositions', []):
            create_position(
                trade_id=trade.id,
                ticker=pos_data.get('ticker'),
                company_name=pos_data.get('companyName', ''),
                position_type='long',
                allocation_percentage=pos_data.get('allocationPercentage', 0),
                rationale=pos_data.get('rationale', ''),
                financial_data=pos_data.get('financialData', {})
            )
        
        # Create short positions
        for pos_data in data.get('shortPositions', []):
            create_position(
                trade_id=trade.id,
                ticker=pos_data.get('ticker'),
                company_name=pos_data.get('companyName', ''),
                position_type='short',
                allocation_percentage=pos_data.get('allocationPercentage', 0),
                rationale=pos_data.get('rationale', ''),
                financial_data=pos_data.get('financialData', {})
            )
        
        # Refresh trade to get positions
        db.session.refresh(trade)
        
        return jsonify({
            'message': 'Trade created successfully',
            'trade': trade.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/<int:trade_id>', methods=['PUT'])
@jwt_required()
def update_trade(trade_id):
    """Update an existing trade"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    trade = get_trade_by_id(trade_id, user.id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update trade fields
        if 'name' in data:
            trade.name = data['name']
        if 'description' in data:
            trade.description = data['description']
        if 'recommendation' in data:
            trade.recommendation = data['recommendation']
        if 'riskLevel' in data:
            trade.risk_level = data['riskLevel']
        if 'analysisText' in data:
            trade.analysis_text = data['analysisText']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Trade updated successfully',
            'trade': trade.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/<int:trade_id>', methods=['DELETE'])
@jwt_required()
def delete_trade_route(trade_id):
    """Delete a trade"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    success = delete_trade(trade_id, user.id)
    
    if success:
        return jsonify({'message': 'Trade deleted successfully'}), 200
    else:
        return jsonify({'error': 'Trade not found'}), 404


# ============================================================================
# HELPER ROUTES
# ============================================================================

@trades_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_trade_stats():
    """Get statistics about user's trades"""
    phone_number = get_jwt_identity()
    user = get_user_by_phone(phone_number)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    trades = get_user_trades(user.id, limit=1000)
    
    stats = {
        'totalTrades': len(trades),
        'recommended': sum(1 for t in trades if t.recommendation == 'RECOMMENDED'),
        'notRecommended': sum(1 for t in trades if t.recommendation == 'NOT_RECOMMENDED'),
        'neutral': sum(1 for t in trades if t.recommendation == 'NEUTRAL'),
        'highRisk': sum(1 for t in trades if t.risk_level == 'HIGH'),
        'moderateRisk': sum(1 for t in trades if t.risk_level == 'MODERATE'),
        'lowRisk': sum(1 for t in trades if t.risk_level == 'LOW')
    }
    
    return jsonify(stats), 200

