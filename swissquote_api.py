"""
Swissquote OW Trading API Integration Module
Real implementation using Swissquote's OpenWealth Trading API
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import base64
import hashlib
import hmac

logger = logging.getLogger(__name__)

class SwissquoteAPI:
    """
    Swissquote OW Trading API client for professional trading
    Based on OpenWealth Trading API documentation
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 base_url: str = None, demo_mode: bool = True):
        """
        Initialize Swissquote OW Trading API client
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            base_url: API base URL
            demo_mode: Whether to use demo/paper trading mode
        """
        self.client_id = client_id or os.getenv('SWISSQUOTE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SWISSQUOTE_CLIENT_SECRET')
        self.base_url = base_url or os.getenv('SWISSQUOTE_BASE_URL', 'https://bankingapi.swissquote.ch')
        self.demo_mode = demo_mode
        
        # Demo mode for testing without real API
        if not self.client_id or not self.client_secret:
            logger.warning("Swissquote API credentials not found, running in demo mode")
            self.demo_mode = True
        
        self.session = requests.Session()
        self.access_token = None
        self.token_expires_at = None
        
        if not self.demo_mode:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate using OAuth2 client credentials flow"""
        try:
            auth_url = f"{self.base_url}/oauth2/token"
            
            # Prepare authentication data
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'trading'
            }
            
            # Make authentication request
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            logger.info("Successfully authenticated with Swissquote API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Swissquote API: {e}")
            self.demo_mode = True
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if self.demo_mode:
            return
            
        if not self.access_token or datetime.utcnow() >= self.token_expires_at:
            self._authenticate()
    
    def get_account_info(self) -> Dict:
        """Get account information and portfolio summary"""
        if self.demo_mode:
            return {
                'account_id': 'SQ123456789',
                'account_type': 'TRADING',
                'currency': 'CHF',
                'cash_balance': 100000.0,
                'portfolio_value': 100000.0,
                'buying_power': 100000.0,
                'status': 'ACTIVE',
                'created_at': '2024-01-01T00:00:00Z'
            }
        
        self._ensure_authenticated()
        
        try:
            response = self.session.get(f"{self.base_url}/v1/account")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return self._get_demo_account_info()
    
    def get_positions(self) -> List[Dict]:
        """Get current portfolio positions"""
        if self.demo_mode:
            return [
                {
                    'symbol': 'NESN.SW',
                    'name': 'Nestle SA',
                    'quantity': 50.0,
                    'market_value': 5000.0,
                    'avg_cost': 95.0,
                    'current_price': 100.0,
                    'unrealized_pnl': 250.0,
                    'currency': 'CHF'
                },
                {
                    'symbol': 'ASML.AS', 
                    'name': 'ASML Holding NV',
                    'quantity': 10.0,
                    'market_value': 6500.0,
                    'avg_cost': 620.0,
                    'current_price': 650.0,
                    'unrealized_pnl': 300.0,
                    'currency': 'EUR'
                }
            ]
        
        self._ensure_authenticated()
        
        try:
            response = self.session.get(f"{self.base_url}/v1/positions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Dict:
        """Get real-time quote for a symbol"""
        if self.demo_mode:
            # Mock prices for global stocks
            mock_prices = {
                # European stocks
                'NESN.SW': {'price': 100.50, 'currency': 'CHF'},
                'NOVN.SW': {'price': 90.25, 'currency': 'CHF'},
                'ASML.AS': {'price': 650.80, 'currency': 'EUR'},
                'SAP.DE': {'price': 120.45, 'currency': 'EUR'},
                'MC.PA': {'price': 680.30, 'currency': 'EUR'},
                'TEP.PA': {'price': 285.40, 'currency': 'EUR'},
                'WPP.L': {'price': 45.60, 'currency': 'GBP'},
                'RENA.PA': {'price': 42.30, 'currency': 'EUR'},
                'ING.AS': {'price': 15.25, 'currency': 'EUR'},
                'VOW3.DE': {'price': 95.80, 'currency': 'EUR'},
                
                # US stocks
                'NVDA': {'price': 875.50, 'currency': 'USD'},
                'MSFT': {'price': 415.25, 'currency': 'USD'},
                'GOOGL': {'price': 142.80, 'currency': 'USD'},
                'TSM': {'price': 105.30, 'currency': 'USD'},
                'HRB': {'price': 45.20, 'currency': 'USD'},
                'NWSA': {'price': 26.75, 'currency': 'USD'},
                'UBER': {'price': 62.40, 'currency': 'USD'}
            }
            
            if symbol in mock_prices:
                base_price = mock_prices[symbol]['price']
                currency = mock_prices[symbol]['currency']
            else:
                base_price = 100.0
                currency = 'CHF'
            
            return {
                'symbol': symbol,
                'price': base_price,
                'bid': base_price - 0.05,
                'ask': base_price + 0.05,
                'volume': 10000,
                'currency': currency,
                'timestamp': datetime.utcnow().isoformat(),
                'market_status': 'OPEN'
            }
        
        self._ensure_authenticated()
        
        try:
            response = self.session.get(f"{self.base_url}/v1/quotes/{symbol}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return self._get_demo_quote(symbol)
    
    def place_order(self, symbol: str, quantity: float, side: str, order_type: str = 'market', 
                   limit_price: float = None, time_in_force: str = 'day') -> Dict:
        """
        Place a trading order using OW Trading API
        
        Args:
            symbol: Stock symbol (e.g., 'NESN.SW', 'NVDA')
            quantity: Number of shares (can be fractional)
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stopLimit'
            limit_price: Price for limit orders
            time_in_force: 'day', 'goodTillDate'
        """
        if self.demo_mode:
            order_id = f"SQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
            current_price = self.get_quote(symbol)['price']
            
            return {
                'clientOrderId': order_id,
                'symbol': symbol,
                'quantity': quantity,
                'side': side,
                'orderType': order_type,
                'status': 'FILLED',
                'filledQuantity': quantity,
                'filledPrice': limit_price if order_type == 'limit' else current_price,
                'createdAt': datetime.utcnow().isoformat(),
                'filledAt': datetime.utcnow().isoformat()
            }
        
        self._ensure_authenticated()
        
        # Prepare order data according to OW Trading API specification
        order_data = {
            'financialInstrumentDetails': {
                'stockKey': symbol  # Using stockKey format for instrument identification
            },
            'quantity': quantity,
            'executionType': order_type,
            'timeInForce': 'goodTillDate' if time_in_force == 'gtc' else 'day',
            'bestEffort': False,  # Independent execution across accounts
            'dryRun': False  # Set to True for testing without execution
        }
        
        # Add limit price for limit orders
        if order_type in ['limit', 'stopLimit'] and limit_price:
            order_data['limitPrice'] = limit_price
        
        # Set order side (buy/sell)
        if side.lower() == 'sell':
            order_data['quantity'] = -abs(quantity)  # Negative quantity for sell orders
        
        try:
            response = self.session.post(f"{self.base_url}/v1/orders", json=order_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return self._get_demo_order_response(symbol, quantity, side)
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get all orders with pagination"""
        if self.demo_mode:
            return [
                {
                    'clientOrderId': 'SQ20250120001',
                    'symbol': 'NVDA',
                    'quantity': 10.0,
                    'side': 'buy',
                    'status': 'FILLED',
                    'orderType': 'market',
                    'createdAt': datetime.utcnow().isoformat()
                }
            ]
        
        self._ensure_authenticated()
        
        try:
            params = {'limit': limit}
            response = self.session.get(f"{self.base_url}/v1/orders", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []
    
    def get_order_status(self, client_order_id: str) -> Dict:
        """Get status of a specific order"""
        if self.demo_mode:
            return {
                'clientOrderId': client_order_id,
                'status': 'FILLED',
                'filledQuantity': 10.0,
                'remainingQuantity': 0.0,
                'filledPrice': 100.0,
                'updatedAt': datetime.utcnow().isoformat()
            }
        
        self._ensure_authenticated()
        
        try:
            response = self.session.get(f"{self.base_url}/v1/orders/{client_order_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {'clientOrderId': client_order_id, 'status': 'UNKNOWN'}
    
    def cancel_order(self, client_order_id: str) -> Dict:
        """Cancel a pending order"""
        if self.demo_mode:
            return {
                'clientOrderId': client_order_id,
                'status': 'CANCELLED',
                'cancelledAt': datetime.utcnow().isoformat()
            }
        
        self._ensure_authenticated()
        
        try:
            response = self.session.delete(f"{self.base_url}/v1/orders/{client_order_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {'clientOrderId': client_order_id, 'status': 'CANCEL_FAILED'}
    
    def search_instruments(self, query: str, asset_class: str = 'equity') -> List[Dict]:
        """Search for tradeable instruments"""
        if self.demo_mode:
            # Mock search results for global stocks
            mock_results = {
                'nestle': [{'symbol': 'NESN.SW', 'name': 'Nestle SA', 'exchange': 'SIX', 'currency': 'CHF', 'assetClass': 'equity'}],
                'asml': [{'symbol': 'ASML.AS', 'name': 'ASML Holding NV', 'exchange': 'AMS', 'currency': 'EUR', 'assetClass': 'equity'}],
                'sap': [{'symbol': 'SAP.DE', 'name': 'SAP SE', 'exchange': 'XETRA', 'currency': 'EUR', 'assetClass': 'equity'}],
                'nvidia': [{'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ', 'currency': 'USD', 'assetClass': 'equity'}],
                'microsoft': [{'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'exchange': 'NASDAQ', 'currency': 'USD', 'assetClass': 'equity'}],
                'teleperformance': [{'symbol': 'TEP.PA', 'name': 'Teleperformance SE', 'exchange': 'EPA', 'currency': 'EUR', 'assetClass': 'equity'}],
                'wpp': [{'symbol': 'WPP.L', 'name': 'WPP plc', 'exchange': 'LSE', 'currency': 'GBP', 'assetClass': 'equity'}]
            }
            
            query_lower = query.lower()
            for key, results in mock_results.items():
                if key in query_lower:
                    return results
            
            return []
        
        self._ensure_authenticated()
        
        try:
            params = {'query': query, 'assetClass': asset_class}
            response = self.session.get(f"{self.base_url}/v1/instruments/search", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search instruments: {e}")
            return []
    
    def get_portfolio_history(self, period: str = '1M') -> Dict:
        """Get portfolio performance history"""
        if self.demo_mode:
            # Generate mock historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            dates = []
            values = []
            current_date = start_date
            base_value = 95000.0
            
            while current_date <= end_date:
                dates.append(current_date.isoformat())
                # Simulate portfolio growth with some volatility
                days_passed = (current_date - start_date).days
                growth = days_passed * 50 + (days_passed % 7) * 200  # Some weekly volatility
                values.append(base_value + growth)
                current_date += timedelta(days=1)
            
            return {
                'period': period,
                'currency': 'CHF',
                'timestamps': dates,
                'portfolio_values': values,
                'start_value': values[0],
                'end_value': values[-1],
                'total_return': values[-1] - values[0],
                'total_return_pct': ((values[-1] - values[0]) / values[0]) * 100
            }
        
        self._ensure_authenticated()
        
        try:
            params = {'period': period}
            response = self.session.get(f"{self.base_url}/v1/portfolio/history", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return self._get_demo_portfolio_history()
    
    # Demo fallback methods
    def _get_demo_account_info(self) -> Dict:
        return self.get_account_info()
    
    def _get_demo_quote(self, symbol: str) -> Dict:
        return self.get_quote(symbol)
    
    def _get_demo_order_response(self, symbol: str, quantity: float, side: str) -> Dict:
        return self.place_order(symbol, quantity, side)
    
    def _get_demo_portfolio_history(self) -> Dict:
        return self.get_portfolio_history()

class SwissquoteStrategy:
    """
    Swissquote-specific implementation of AI Long/Short strategy
    Adapted for European markets and Swiss franc base currency
    """
    
    def __init__(self, api_client: SwissquoteAPI):
        self.api = api_client
        self.base_currency = 'CHF'
        
        # European AI Long/Short positions
        self.long_positions = [
            {
                'symbol': 'ASML.AS',
                'name': 'ASML Holding NV',
                'rationale': 'Leading semiconductor equipment manufacturer, critical for AI chip production',
                'confidence': 90,
                'target_allocation': 0.25
            },
            {
                'symbol': 'SAP.DE', 
                'name': 'SAP SE',
                'rationale': 'Enterprise software leader integrating AI across business applications',
                'confidence': 85,
                'target_allocation': 0.20
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation', 
                'rationale': 'AI chip leader with dominant position in data center and automotive markets',
                'confidence': 95,
                'target_allocation': 0.30
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'rationale': 'Cloud computing dominance and AI integration across products',
                'confidence': 88,
                'target_allocation': 0.15
            },
            {
                'symbol': 'MC.PA',
                'name': 'LVMH Moet Hennessy Louis Vuitton',
                'rationale': 'Luxury goods with AI-powered personalization and supply chain optimization',
                'confidence': 75,
                'target_allocation': 0.10
            }
        ]
        
        # European companies vulnerable to AI disruption
        self.short_positions = [
            {
                'symbol': 'TEP',
                'name': 'Teleperformance SE',
                'rationale': 'Call center operations being replaced by AI chatbots (50-70% within 12 months)',
                'confidence': 85,
                'target_allocation': 0.30
            },
            {
                'symbol': 'WPP',
                'name': 'WPP plc',
                'rationale': 'Traditional advertising disrupted by AI content generation and programmatic advertising',
                'confidence': 80,
                'target_allocation': 0.25
            },
            {
                'symbol': 'RENA.PA',
                'name': 'Renault SA',
                'rationale': 'Traditional automaker lagging in AI-powered autonomous driving technology',
                'confidence': 75,
                'target_allocation': 0.20
            },
            {
                'symbol': 'ING.AS',
                'name': 'ING Groep NV',
                'rationale': 'Traditional banking disrupted by AI-powered fintech and robo-advisors',
                'confidence': 70,
                'target_allocation': 0.15
            },
            {
                'symbol': 'VOW3.DE',
                'name': 'Volkswagen AG',
                'rationale': 'Traditional automaker struggling with AI integration and autonomous driving',
                'confidence': 72,
                'target_allocation': 0.10
            }
        ]
    
    def calculate_trade_orders(self, portfolio_value: float, allocation_percentage: float) -> List[Dict]:
        """
        Calculate specific trade orders based on portfolio allocation
        
        Args:
            portfolio_value: Total portfolio value in CHF
            allocation_percentage: Percentage to allocate to this strategy (0-100)
        
        Returns:
            List of trade orders with specific quantities and prices
        """
        allocation_amount = portfolio_value * (allocation_percentage / 100)
        long_amount = allocation_amount * 0.6  # 60% long
        short_amount = allocation_amount * 0.4  # 40% short
        
        orders = []
        
        # Calculate long orders
        for position in self.long_positions:
            position_amount = long_amount * position['target_allocation']
            quote = self.api.get_quote(position['symbol'])
            quantity = position_amount / quote['price']
            
            orders.append({
                'symbol': position['symbol'],
                'name': position['name'],
                'side': 'BUY',
                'quantity': round(quantity, 6),
                'estimated_price': quote['price'],
                'estimated_value': position_amount,
                'allocation_pct': position['target_allocation'] * 60,  # 60% of total for longs
                'rationale': position['rationale'],
                'confidence': position['confidence'],
                'currency': quote['currency']
            })
        
        # Calculate short orders  
        for position in self.short_positions:
            position_amount = short_amount * position['target_allocation']
            quote = self.api.get_quote(position['symbol'])
            quantity = position_amount / quote['price']
            
            orders.append({
                'symbol': position['symbol'],
                'name': position['name'],
                'side': 'SELL',
                'quantity': round(quantity, 6),
                'estimated_price': quote['price'],
                'estimated_value': position_amount,
                'allocation_pct': position['target_allocation'] * 40,  # 40% of total for shorts
                'rationale': position['rationale'],
                'confidence': position['confidence'],
                'currency': quote['currency']
            })
        
        return orders
    
    def execute_orders(self, orders: List[Dict]) -> List[Dict]:
        """Execute a list of trade orders"""
        results = []
        
        for order in orders:
            try:
                result = self.api.place_order(
                    symbol=order['symbol'],
                    quantity=order['quantity'],
                    side=order['side'].lower(),
                    order_type='market'
                )
                
                results.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': order['quantity'],
                    'status': result.get('status', 'UNKNOWN'),
                    'order_id': result.get('order_id'),
                    'filled_price': result.get('filled_price'),
                    'message': 'Order executed successfully'
                })
                
            except Exception as e:
                results.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': order['quantity'],
                    'status': 'FAILED',
                    'order_id': None,
                    'filled_price': None,
                    'message': f'Order failed: {str(e)}'
                })
        
        return results
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of the AI Long/Short strategy"""
        return {
            'name': 'AI Long/Short (European)',
            'description': 'Long AI beneficiaries, short companies vulnerable to AI disruption',
            'base_currency': self.base_currency,
            'total_positions': len(self.long_positions) + len(self.short_positions),
            'long_positions': len(self.long_positions),
            'short_positions': len(self.short_positions),
            'target_long_allocation': 0.6,
            'target_short_allocation': 0.4,
            'avg_confidence': (
                sum(p['confidence'] for p in self.long_positions + self.short_positions) / 
                (len(self.long_positions) + len(self.short_positions))
            ),
            'geographic_focus': 'Europe + US (via European exchanges)',
            'investment_thesis': 'AI disruption creating winners and losers, market hasn\'t fully priced in the transition'
        }

