"""
Global AI Long/Short Strategy
Unified strategy accessible to both US and European users through Alpaca and Swissquote
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GlobalAILongShortStrategy:
    """
    Unified Global AI Long/Short Strategy
    
    Same positions available to all users regardless of broker or location.
    Combines best AI beneficiaries and AI disruption targets from global markets.
    """
    
    def __init__(self, broker_api=None):
        self.api = broker_api
        self.strategy_name = "Global AI Long/Short"
        self.description = "Global strategy: Long AI beneficiaries, short companies vulnerable to AI disruption"
        
        # Unified global positions - same for all users
        self.long_positions = [
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'rationale': 'AI chip leader with dominant position in data center, automotive, and edge computing',
                'confidence': 95,
                'target_allocation': 0.25,
                'market': 'US',
                'currency': 'USD'
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'rationale': 'Cloud computing dominance with AI integration across Azure, Office, and GitHub Copilot',
                'confidence': 88,
                'target_allocation': 0.20,
                'market': 'US',
                'currency': 'USD'
            },
            {
                'symbol': 'ASML',
                'name': 'ASML Holding NV',
                'rationale': 'Critical semiconductor equipment manufacturer for AI chip production, monopoly position',
                'confidence': 90,
                'target_allocation': 0.20,
                'market': 'EU',
                'currency': 'EUR',
                'alpaca_symbol': 'ASML',  # US ADR
                'swissquote_symbol': 'ASML.AS'  # Amsterdam listing
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'rationale': 'AI research leader with Bard, DeepMind, and AI-powered search and advertising',
                'confidence': 85,
                'target_allocation': 0.15,
                'market': 'US',
                'currency': 'USD'
            },
            {
                'symbol': 'TSM',
                'name': 'Taiwan Semiconductor Manufacturing',
                'rationale': 'World\'s largest contract chip manufacturer, produces most advanced AI chips',
                'confidence': 87,
                'target_allocation': 0.20,
                'market': 'ASIA',
                'currency': 'USD',
                'alpaca_symbol': 'TSM',  # US ADR
                'swissquote_symbol': 'TSM'  # Available on European exchanges
            }
        ]
        
        # Global AI disruption targets - companies vulnerable to AI replacement
        self.short_positions = [
            {
                'symbol': 'TEP',
                'name': 'Teleperformance SE',
                'rationale': 'Call center operations being replaced by AI chatbots and virtual assistants (50-70% job displacement within 12 months)',
                'confidence': 85,
                'target_allocation': 0.25,
                'market': 'EU',
                'currency': 'EUR',
                'alpaca_symbol': 'TEP',  # May be available as ADR
                'swissquote_symbol': 'TEP.PA'  # Paris listing
            },
            {
                'symbol': 'HRB',
                'name': 'H&R Block Inc.',
                'rationale': 'Tax preparation services disrupted by AI-powered tax software and automation',
                'confidence': 80,
                'target_allocation': 0.20,
                'market': 'US',
                'currency': 'USD'
            },
            {
                'symbol': 'NWSA',
                'name': 'News Corporation',
                'rationale': 'Traditional media disrupted by AI content generation and personalized news aggregation',
                'confidence': 75,
                'target_allocation': 0.20,
                'market': 'US',
                'currency': 'USD'
            },
            {
                'symbol': 'WPP',
                'name': 'WPP plc',
                'rationale': 'Traditional advertising agency disrupted by AI-powered content creation and programmatic advertising',
                'confidence': 78,
                'target_allocation': 0.20,
                'market': 'EU',
                'currency': 'GBP',
                'alpaca_symbol': 'WPP',  # US ADR
                'swissquote_symbol': 'WPP.L'  # London listing
            },
            {
                'symbol': 'UBER',
                'name': 'Uber Technologies Inc.',
                'rationale': 'Rideshare model vulnerable to autonomous vehicle disruption and AI-optimized logistics',
                'confidence': 72,
                'target_allocation': 0.15,
                'market': 'US',
                'currency': 'USD'
            }
        ]
    
    def get_broker_symbol(self, position: Dict, broker_type: str) -> str:
        """
        Get the appropriate symbol for the broker
        
        Args:
            position: Position dictionary with symbol information
            broker_type: 'alpaca' or 'swissquote'
        
        Returns:
            Appropriate symbol for the broker
        """
        if broker_type == 'alpaca':
            return position.get('alpaca_symbol', position['symbol'])
        elif broker_type == 'swissquote':
            return position.get('swissquote_symbol', position['symbol'])
        else:
            return position['symbol']
    
    def calculate_trade_orders(self, portfolio_value: float, allocation_percentage: float, broker_type: str = 'alpaca') -> List[Dict]:
        """
        Calculate trade orders for the global strategy
        
        Args:
            portfolio_value: Total portfolio value
            allocation_percentage: Percentage to allocate to this strategy (0-100)
            broker_type: 'alpaca' or 'swissquote'
        
        Returns:
            List of trade orders with broker-appropriate symbols
        """
        allocation_amount = portfolio_value * (allocation_percentage / 100)
        long_amount = allocation_amount * 0.6  # 60% long
        short_amount = allocation_amount * 0.4  # 40% short
        
        orders = []
        
        # Calculate long orders
        for position in self.long_positions:
            position_amount = long_amount * position['target_allocation']
            broker_symbol = self.get_broker_symbol(position, broker_type)
            
            # Get quote using broker-appropriate symbol
            if self.api:
                if hasattr(self.api, 'get_quote'):
                    quote = self.api.get_quote(broker_symbol)
                    current_price = quote.get('price', quote.get('ask', 100.0))
                else:
                    # Fallback for different API structures
                    current_price = 100.0
            else:
                # Demo mode - use mock prices
                current_price = self._get_mock_price(broker_symbol)
            
            quantity = position_amount / current_price
            
            orders.append({
                'symbol': broker_symbol,
                'name': position['name'],
                'side': 'BUY',
                'quantity': round(quantity, 6),
                'estimated_price': current_price,
                'estimated_value': position_amount,
                'allocation_pct': position['target_allocation'] * 60,  # 60% of total for longs
                'rationale': position['rationale'],
                'confidence': position['confidence'],
                'currency': position['currency'],
                'market': position['market']
            })
        
        # Calculate short orders
        for position in self.short_positions:
            position_amount = short_amount * position['target_allocation']
            broker_symbol = self.get_broker_symbol(position, broker_type)
            
            # Get quote using broker-appropriate symbol
            if self.api:
                if hasattr(self.api, 'get_quote'):
                    quote = self.api.get_quote(broker_symbol)
                    current_price = quote.get('price', quote.get('ask', 100.0))
                else:
                    current_price = 100.0
            else:
                # Demo mode - use mock prices
                current_price = self._get_mock_price(broker_symbol)
            
            quantity = position_amount / current_price
            
            orders.append({
                'symbol': broker_symbol,
                'name': position['name'],
                'side': 'SELL',
                'quantity': round(quantity, 6),
                'estimated_price': current_price,
                'estimated_value': position_amount,
                'allocation_pct': position['target_allocation'] * 40,  # 40% of total for shorts
                'rationale': position['rationale'],
                'confidence': position['confidence'],
                'currency': position['currency'],
                'market': position['market']
            })
        
        return orders
    
    def _get_mock_price(self, symbol: str) -> float:
        """Get mock prices for demo mode"""
        mock_prices = {
            # US stocks
            'NVDA': 875.50,
            'MSFT': 415.25,
            'GOOGL': 142.80,
            'TSM': 105.30,
            'HRB': 45.20,
            'NWSA': 26.75,
            'UBER': 62.40,
            
            # European stocks (Alpaca ADRs)
            'ASML': 950.80,
            'WPP': 45.60,
            'TEP': 285.40,
            
            # European stocks (Swissquote symbols)
            'ASML.AS': 650.80,
            'WPP.L': 8.50,
            'TEP.PA': 285.40,
        }
        
        return mock_prices.get(symbol, 100.0)
    
    def execute_orders(self, orders: List[Dict]) -> List[Dict]:
        """Execute trade orders through the broker API"""
        if not self.api:
            # Demo mode - simulate execution
            return self._simulate_execution(orders)
        
        results = []
        for order in orders:
            try:
                if hasattr(self.api, 'place_order'):
                    # Swissquote API
                    result = self.api.place_order(
                        symbol=order['symbol'],
                        quantity=order['quantity'],
                        side=order['side'].lower(),
                        order_type='market'
                    )
                else:
                    # Alpaca API
                    result = self.api.submit_order(
                        symbol=order['symbol'],
                        qty=order['quantity'],
                        side=order['side'].lower(),
                        type='market',
                        time_in_force='day'
                    )
                
                results.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': order['quantity'],
                    'status': 'SUBMITTED',
                    'order_id': getattr(result, 'id', result.get('order_id')),
                    'message': 'Order submitted successfully'
                })
                
            except Exception as e:
                results.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'quantity': order['quantity'],
                    'status': 'FAILED',
                    'order_id': None,
                    'message': f'Order failed: {str(e)}'
                })
        
        return results
    
    def _simulate_execution(self, orders: List[Dict]) -> List[Dict]:
        """Simulate order execution for demo mode"""
        return [
            {
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['quantity'],
                'status': 'SIMULATED',
                'order_id': f"demo_{order['symbol']}_{hash(str(order)) % 10000}",
                'filled_price': order['estimated_price'],
                'message': 'Order simulated successfully'
            }
            for order in orders
        ]
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of the global AI Long/Short strategy"""
        all_positions = self.long_positions + self.short_positions
        
        # Count markets
        markets = set(pos['market'] for pos in all_positions)
        currencies = set(pos['currency'] for pos in all_positions)
        
        return {
            'name': self.strategy_name,
            'description': self.description,
            'total_positions': len(all_positions),
            'long_positions': len(self.long_positions),
            'short_positions': len(self.short_positions),
            'target_long_allocation': 0.6,
            'target_short_allocation': 0.4,
            'avg_confidence': sum(pos['confidence'] for pos in all_positions) / len(all_positions),
            'markets': list(markets),
            'currencies': list(currencies),
            'geographic_scope': 'Global (US, Europe, Asia)',
            'investment_thesis': 'AI disruption creating global winners and losers across all markets',
            'positions': [
                {
                    'symbol': pos['symbol'],
                    'name': pos['name'],
                    'side': 'long' if pos in self.long_positions else 'short',
                    'weight': pos['target_allocation'] * (0.6 if pos in self.long_positions else 0.4),
                    'rationale': pos['rationale'],
                    'confidence': pos['confidence'],
                    'market': pos['market'],
                    'currency': pos['currency']
                }
                for pos in all_positions
            ]
        }
    
    def get_positions_by_market(self) -> Dict:
        """Get positions grouped by market for analysis"""
        markets = {}
        
        for pos_list, side in [(self.long_positions, 'long'), (self.short_positions, 'short')]:
            for pos in pos_list:
                market = pos['market']
                if market not in markets:
                    markets[market] = {'long': [], 'short': []}
                markets[market][side].append(pos)
        
        return markets

