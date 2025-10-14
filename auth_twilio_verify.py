"""
Authentication service for RationalMarkets
Implements phone-based authentication with Twilio Verify API and JWT tokens
"""

import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from twilio.rest import Client
from models import User
from database import DatabaseSession
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with phone verification using Twilio Verify API and JWT"""
    
    def __init__(self):
        # JWT configuration
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration_hours = 24 * 7  # 7 days
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        # Initialize Twilio client if credentials are available
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not found - SMS verification disabled")
    
    def normalize_phone_number(self, phone_number):
        """Normalize phone number to E.164 format"""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Add + prefix if not present
        if not phone_number.startswith('+'):
            phone_number = '+' + digits
        
        return phone_number
    
    def request_verification_code(self, phone_number):
        """
        Request a verification code for phone number using Twilio Verify API
        
        Args:
            phone_number: Phone number in E.164 format
        
        Returns:
            Dict with success status and message
        """
        try:
            # Normalize phone number
            phone_number = self.normalize_phone_number(phone_number)
            
            if not self.twilio_client or not self.twilio_verify_service_sid:
                # Development mode - log a fake code
                logger.info(f"DEV MODE: Verification code for {phone_number}: 123456")
                logger.warning("Twilio Verify not configured - using dev mode")
                return {
                    'success': True,
                    'message': 'Verification code sent (dev mode - use 123456)'
                }
            
            # Use Twilio Verify API to send code
            verification = self.twilio_client.verify \
                .v2 \
                .services(self.twilio_verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            logger.info(f"Verification sent to {phone_number}: {verification.status}")
            
            return {
                'success': True,
                'message': 'Verification code sent successfully'
            }
        
        except Exception as e:
            logger.error(f"Error requesting verification code: {e}")
            return {
                'success': False,
                'message': f'Failed to send verification code: {str(e)}'
            }
    
    def verify_code(self, phone_number, code):
        """
        Verify the code for phone number using Twilio Verify API
        
        Args:
            phone_number: Phone number in E.164 format
            code: Verification code to check
        
        Returns:
            Dict with success status, JWT token, and user data
        """
        try:
            # Normalize phone number
            phone_number = self.normalize_phone_number(phone_number)
            
            # Development mode check
            if not self.twilio_client or not self.twilio_verify_service_sid:
                logger.info(f"DEV MODE: Verifying code for {phone_number}")
                # In dev mode, accept 123456 as valid code
                if code != '123456':
                    return {
                        'success': False,
                        'message': 'Invalid verification code (dev mode - use 123456)'
                    }
            else:
                # Use Twilio Verify API to check code
                verification_check = self.twilio_client.verify \
                    .v2 \
                    .services(self.twilio_verify_service_sid) \
                    .verification_checks \
                    .create(to=phone_number, code=code)
                
                logger.info(f"Verification check for {phone_number}: {verification_check.status}")
                
                if verification_check.status != 'approved':
                    return {
                        'success': False,
                        'message': 'Invalid or expired verification code'
                    }
            
            # Code verified - get or create user
            with DatabaseSession() as session:
                user = session.query(User).filter_by(phone_number=phone_number).first()
                
                if not user:
                    # Create new user
                    user = User(
                        phone_number=phone_number,
                        is_verified=True,
                        last_login=datetime.utcnow()
                    )
                    session.add(user)
                    session.commit()
                    logger.info(f"New user created: {phone_number}")
                else:
                    # Update existing user
                    user.is_verified = True
                    user.last_login = datetime.utcnow()
                    session.commit()
                    logger.info(f"User logged in: {phone_number}")
                
                # Generate JWT token
                token = self.generate_jwt_token(user)
                
                return {
                    'success': True,
                    'message': 'Verification successful',
                    'token': token,
                    'user': {
                        'id': str(user.id),
                        'phone_number': user.phone_number,
                        'email': user.email,
                        'full_name': user.full_name,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    }
                }
        
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return {
                'success': False,
                'message': f'Verification failed: {str(e)}'
            }
    
    def generate_jwt_token(self, user):
        """Generate JWT token for user"""
        payload = {
            'user_id': str(user.id),
            'phone_number': user.phone_number,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token):
        """
        Verify JWT token and return user data
        
        Args:
            token: JWT token string
        
        Returns:
            Dict with user data if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return {
                'id': payload['user_id'],
                'phoneNumber': payload['phone_number']
            }
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None


# Global auth service instance
_auth_service = None

def get_auth_service():
    """Get or create the global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# Decorators for route protection
def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        token = auth_header.split(' ')[1]
        auth_service = get_auth_service()
        user = auth_service.verify_jwt_token(token)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Attach user to request
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication (user data available if authenticated)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            auth_service = get_auth_service()
            user = auth_service.verify_jwt_token(token)
            request.user = user
        else:
            request.user = None
        
        return f(*args, **kwargs)
    
    return decorated_function

