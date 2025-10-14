"""
Twilio Phone Authentication Service
Implements phone-based OTP authentication using Twilio Verify API
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class TwilioAuthService:
    """Twilio Verify API service for phone authentication"""
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.verify_sid = os.environ.get('TWILIO_VERIFY_SID')
        
        if not all([self.account_sid, self.auth_token, self.verify_sid]):
            print("⚠️  Warning: Twilio credentials not configured. Using mock mode.")
            self.client = None
            self.mock_mode = True
        else:
            self.client = Client(self.account_sid, self.auth_token)
            self.mock_mode = False
    
    def send_verification_code(self, phone_number):
        """
        Send OTP verification code to phone number
        
        Args:
            phone_number (str): Phone number in E.164 format (e.g., +1234567890)
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'sid': str (verification SID)
            }
        """
        # Mock mode for development
        if self.mock_mode:
            print(f"📱 [MOCK] Sending OTP to {phone_number}: 123456")
            return {
                'success': True,
                'message': 'Verification code sent (mock mode)',
                'sid': 'mock_verification_sid'
            }
        
        try:
            verification = self.client.verify \
                .v2 \
                .services(self.verify_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            return {
                'success': True,
                'message': 'Verification code sent successfully',
                'sid': verification.sid
            }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'message': f'Failed to send verification code: {str(e)}',
                'sid': None
            }
    
    def verify_code(self, phone_number, code):
        """
        Verify OTP code for phone number
        
        Args:
            phone_number (str): Phone number in E.164 format
            code (str): 6-digit OTP code
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'verified': bool
            }
        """
        # Mock mode for development
        if self.mock_mode:
            # Accept "123456" as valid code in mock mode
            if code == "123456":
                print(f"✅ [MOCK] Phone {phone_number} verified successfully")
                return {
                    'success': True,
                    'message': 'Phone number verified (mock mode)',
                    'verified': True
                }
            else:
                print(f"❌ [MOCK] Invalid code for {phone_number}")
                return {
                    'success': False,
                    'message': 'Invalid verification code (mock mode)',
                    'verified': False
                }
        
        try:
            verification_check = self.client.verify \
                .v2 \
                .services(self.verify_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            
            if verification_check.status == 'approved':
                return {
                    'success': True,
                    'message': 'Phone number verified successfully',
                    'verified': True
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid verification code',
                    'verified': False
                }
        
        except TwilioRestException as e:
            return {
                'success': False,
                'message': f'Verification failed: {str(e)}',
                'verified': False
            }


# Global instance
twilio_auth = TwilioAuthService()

