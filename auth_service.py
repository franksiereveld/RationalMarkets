"""
Authentication service using Twilio Verify API
Handles phone verification and user authentication
"""

import os
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token

# Twilio client will be initialized when credentials are available
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Warning: Twilio library not installed. Install with: pip install twilio")


class AuthService:
    """Authentication service for phone verification"""
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        if TWILIO_AVAILABLE and self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("Warning: Twilio authentication is disabled. Set TWILIO credentials in .env")
    
    def is_enabled(self):
        """Check if Twilio authentication is enabled"""
        return self.enabled
    
    def send_verification_code(self, phone_number):
        """
        Send OTP verification code to phone number
        
        Args:
            phone_number (str): Phone number in E.164 format (e.g., +15551234567)
            
        Returns:
            dict: Status of verification request
        """
        if not self.enabled:
            # Development mode - return mock success
            return {
                'success': True,
                'status': 'pending',
                'message': f'[DEV MODE] Verification code would be sent to {phone_number}. Use code: 123456',
                'dev_mode': True
            }
        
        try:
            verification = self.client.verify.v2 \
                .services(self.verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            return {
                'success': True,
                'status': verification.status,
                'message': f'Verification code sent to {phone_number}',
                'dev_mode': False
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send verification code'
            }
    
    def verify_code(self, phone_number, code):
        """
        Verify the OTP code entered by user
        
        Args:
            phone_number (str): Phone number in E.164 format
            code (str): 6-digit verification code
            
        Returns:
            dict: Verification result with JWT token if successful
        """
        if not self.enabled:
            # Development mode - accept code 123456
            if code == '123456':
                access_token = create_access_token(
                    identity=phone_number,
                    expires_delta=timedelta(days=30)
                )
                
                return {
                    'success': True,
                    'verified': True,
                    'access_token': access_token,
                    'phone_number': phone_number,
                    'dev_mode': True,
                    'message': '[DEV MODE] Verification successful'
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'message': '[DEV MODE] Invalid code. Use: 123456',
                    'dev_mode': True
                }
        
        try:
            verification_check = self.client.verify.v2 \
                .services(self.verify_service_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            
            if verification_check.status == 'approved':
                # Create JWT token for authenticated session
                access_token = create_access_token(
                    identity=phone_number,
                    expires_delta=timedelta(days=30)
                )
                
                return {
                    'success': True,
                    'verified': True,
                    'access_token': access_token,
                    'phone_number': phone_number,
                    'dev_mode': False
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'message': 'Invalid verification code',
                    'dev_mode': False
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Verification failed'
            }
    
    def validate_phone_number(self, phone_number):
        """
        Validate phone number format
        
        Args:
            phone_number (str): Phone number to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not phone_number:
            return False, "Phone number is required"
        
        # Check E.164 format
        if not phone_number.startswith('+'):
            return False, "Phone number must start with + and country code (e.g., +1 for US)"
        
        # Remove + and check if remaining is digits
        digits = phone_number[1:]
        if not digits.isdigit():
            return False, "Phone number must contain only digits after +"
        
        # Check length (E.164 allows 1-15 digits)
        if len(digits) < 10 or len(digits) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        return True, None


# Global instance
auth_service = AuthService()

