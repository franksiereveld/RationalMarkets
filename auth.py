"""
Authentication service for RationalMarkets
Implements phone-based authentication with Twilio SMS verification and JWT tokens
"""

import os
import jwt
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from twilio.rest import Client
from models import User
from database import DatabaseSession
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with phone verification and JWT"""
    
    def __init__(self):
        # JWT configuration
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration_hours = 24 * 7  # 7 days
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
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
        
        # Verification code settings
        self.code_length = 6
        self.code_expiration_minutes = 10
    
    def generate_verification_code(self):
        """Generate a random 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def send_verification_sms(self, phone_number, code):
        """
        Send verification code via SMS
        
        Args:
            phone_number: Phone number in E.164 format (e.g., +1234567890)
            code: Verification code to send
        
        Returns:
            True if SMS sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.error("Twilio client not initialized - cannot send SMS")
            # In development, just log the code
            logger.info(f"DEV MODE: Verification code for {phone_number}: {code}")
            return True  # Return True in dev mode for testing
        
        try:
            message = self.twilio_client.messages.create(
                body=f"Your RationalMarkets verification code is: {code}. Valid for {self.code_expiration_minutes} minutes.",
                from_=self.twilio_phone_number,
                to=phone_number
            )
            logger.info(f"SMS sent successfully to {phone_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False
    
    def request_verification_code(self, phone_number):
        """
        Request a verification code for phone number
        
        Args:
            phone_number: Phone number in E.164 format
        
        Returns:
            Dict with success status and message
        """
        try:
            # Normalize phone number
            phone_number = self.normalize_phone_number(phone_number)
            
            # Generate verification code
            code = self.generate_verification_code()
            expiration = datetime.utcnow() + timedelta(minutes=self.code_expiration_minutes)
            
            # Store code in database
            with DatabaseSession() as session:
                user = session.query(User).filter_by(phone_number=phone_number).first()
                
                if not user:
                    # Create new user
                    user = User(
                        phone_number=phone_number,
                        verification_code=code,
                        verification_expires_at=expiration,
                        is_verified=False
                    )
                    session.add(user)
                else:
                    # Update existing user
                    user.verification_code = code
                    user.verification_expires_at = expiration
                
                session.commit()
                user_id = str(user.id)
            
            # Send SMS
            sms_sent = self.send_verification_sms(phone_number, code)
            
            if not sms_sent:
                return {
                    'success': False,
                    'message': 'Failed to send verification code. Please try again.'
                }
            
            return {
                'success': True,
                'message': f'Verification code sent to {phone_number}',
                'userId': user_id,
                'expiresIn': self.code_expiration_minutes * 60  # seconds
            }
        
        except Exception as e:
            logger.error(f"Error requesting verification code: {e}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again.'
            }
    
    def verify_code(self, phone_number, code):
        """
        Verify the code entered by user
        
        Args:
            phone_number: Phone number in E.164 format
            code: Verification code entered by user
        
        Returns:
            Dict with success status, JWT token if successful
        """
        try:
            phone_number = self.normalize_phone_number(phone_number)
            
            with DatabaseSession() as session:
                user = session.query(User).filter_by(phone_number=phone_number).first()
                
                if not user:
                    return {
                        'success': False,
                        'message': 'Phone number not found. Please request a new code.'
                    }
                
                # Check if code matches
                if user.verification_code != code:
                    return {
                        'success': False,
                        'message': 'Invalid verification code. Please try again.'
                    }
                
                # Check if code is expired
                if user.verification_expires_at < datetime.utcnow():
                    return {
                        'success': False,
                        'message': 'Verification code expired. Please request a new code.'
                    }
                
                # Mark user as verified
                user.is_verified = True
                user.last_login = datetime.utcnow()
                user.verification_code = None  # Clear the code
                user.verification_expires_at = None
                session.commit()
                
                user_data = user.to_dict()
            
            # Generate JWT token
            token = self.generate_jwt_token(user_data['id'])
            
            return {
                'success': True,
                'message': 'Phone number verified successfully',
                'token': token,
                'user': user_data
            }
        
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again.'
            }
    
    def generate_jwt_token(self, user_id):
        """
        Generate JWT token for authenticated user
        
        Args:
            user_id: User ID (UUID as string)
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token):
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Dict with user_id if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def normalize_phone_number(self, phone_number):
        """
        Normalize phone number to E.164 format
        
        Args:
            phone_number: Phone number in various formats
        
        Returns:
            Normalized phone number (e.g., +1234567890)
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present (assume US +1)
        if len(digits) == 10:
            digits = '1' + digits
        
        return '+' + digits
    
    def get_user_from_token(self, token):
        """
        Get user object from JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            User object if valid, None if invalid
        """
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        try:
            import uuid as uuid_module
            with DatabaseSession() as session:
                # Convert string UUID to UUID object
                user_id = uuid_module.UUID(payload['user_id'])
                user = session.query(User).filter_by(id=user_id).first()
                if user and user.is_active:
                    user_data = user.to_dict()
                    return user_data
                return None
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global auth service instance
_auth_service = None


def get_auth_service():
    """Get or create global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# Flask decorator for protected routes
def require_auth(f):
    """
    Decorator to protect routes that require authentication
    
    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user = request.user  # User data available here
            return jsonify({'message': 'Success'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'message': 'Authorization header missing'
            }), 401
        
        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'message': 'Invalid authorization header format'
            }), 401
        
        # Verify token and get user
        auth_service = get_auth_service()
        user = auth_service.get_user_from_token(token)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Attach user to request object
        request.user = user
        
        return f(*args, **kwargs)
    
    return decorated_function


# Optional decorator for routes that work with or without auth
def optional_auth(f):
    """
    Decorator for routes that work with or without authentication
    If authenticated, user data is available in request.user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                auth_service = get_auth_service()
                user = auth_service.get_user_from_token(token)
                request.user = user
            except:
                request.user = None
        else:
            request.user = None
        
        return f(*args, **kwargs)
    
    return decorated_function


if __name__ == '__main__':
    # Test authentication service
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Authentication Service...")
    auth = AuthService()
    
    # Test phone number normalization
    test_numbers = [
        '1234567890',
        '+1234567890',
        '(123) 456-7890',
        '+1 (123) 456-7890'
    ]
    
    print("\nPhone number normalization:")
    for number in test_numbers:
        normalized = auth.normalize_phone_number(number)
        print(f"  {number} → {normalized}")
    
    # Test verification code generation
    print(f"\nGenerated verification code: {auth.generate_verification_code()}")
    
    # Test JWT token
    test_user_id = 'test-user-123'
    token = auth.generate_jwt_token(test_user_id)
    print(f"\nGenerated JWT token: {token[:50]}...")
    
    payload = auth.verify_jwt_token(token)
    print(f"Decoded payload: {payload}")
    
    print("\n✅ Authentication service tests completed!")

