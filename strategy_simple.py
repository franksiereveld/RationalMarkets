"""
AI Long/Short Investment Strategy MVP - Simplified Version

This module implements a simplified AI-driven long/short equity strategy
that can work with or without Alpaca API integration.
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import requests


@dataclass
class Position:
    """Represents a single position in the strategy"""
    symbol: str
    side: str  # 'long' or 'short'
    weight: float  # Percentage of strategy allocation
    confidence: float  # AI confidence score (0-1)
    rationale: str  # Human-readable explanation


@dataclass
class PortfolioAllocation:
    """Represents user's allocation to the strategy"""
    user_id: str
    strategy_name: str
    allocation_percentage: float  # Percentage of total portfolio
    total_portfolio_value: float
    allocated_amount: float


class AILongShortStrategy:
    """
    AI Long/Short Strategy Implementation - Simplified Version
    
    This strategy selects stocks for long and short positions based on
    AI analysis of market trends, fundamentals, and technical indicators.
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None):
        """Initialize strategy with optional Alpaca API credentials"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url or 'https://paper-api.alpaca.markets'
        self.strategy_name = "AI Long/Short"
        self.last_updated = datetime.now()
        
        # Initialize strategy positions
        self.positions = self._get_current_strategy_positions()
        
        # Mock price data for demo mode
        self.mock_prices = {
            # Long positions - AI beneficiaries
            'NVDA': 875.50, 'MSFT': 415.25, 'GOOGL': 142.80, 'TSLA': 248.75, 'AMZN': 145.30,
            # Short positions - AI disruption targets
            'TEP': 85.20, 'HRB': 52.40, 'CNXC': 68.75, 'NWSA': 24.15, 'NYT': 45.80
        }
    
    def _get_current_strategy_positions(self) -> List[Position]:
        """
        Define current AI-selected positions for the strategy
        
        In a real implementation, this would call ML models and analysis engines.
        For MVP, we use a curated list based on market analysis.
        """
        return [
            # Long Positions (60% of strategy allocation)
            Position(
                symbol="NVDA",
                side="long",
                weight=0.20,  # 20% of strategy
                confidence=0.92,
                rationale="AI chip leader with strong growth in data center and automotive markets"
            ),
            Position(
                symbol="MSFT",
                side="long", 
                weight=0.15,  # 15% of strategy
                confidence=0.88,
                rationale="Cloud computing dominance and successful AI integration across products"
            ),
            Position(
                symbol="GOOGL",
                side="long",
                weight=0.10,  # 10% of strategy
                confidence=0.85,
                rationale="Search monopoly provides cash flow for AI development and innovation"
            ),
            Position(
                symbol="TSLA",
                side="long",
                weight=0.10,  # 10% of strategy
                confidence=0.78,
                rationale="EV market leadership and potential in autonomous driving technology"
            ),
            Position(
                symbol="AMZN",
                side="long",
                weight=0.05,  # 5% of strategy
                confidence=0.82,
                rationale="AWS growth and e-commerce efficiency improvements"
            ),
            
            # Short Positions (40% of strategy allocation) - AI Disruption Targets
            Position(
                symbol="TEP",  # Teleperformance - Call center services
                side="short",
                weight=0.12,  # 12% of strategy
                confidence=0.85,
                rationale="AI chatbots and automation replacing 50-70% of call center operations within 12 months"
            ),
            Position(
                symbol="HRB",  # H&R Block - Tax preparation
                side="short",
                weight=0.10,  # 10% of strategy
                confidence=0.78,
                rationale="AI tax preparation tools eliminating need for human tax preparers for simple returns"
            ),
            Position(
                symbol="CNXC",  # Concentrix - Business process outsourcing
                side="short",
                weight=0.08,  # 8% of strategy
                confidence=0.82,
                rationale="AI automation disrupting traditional BPO services and customer support operations"
            ),
            Position(
                symbol="NWSA",  # News Corporation - Traditional media
                side="short",
                weight=0.06,  # 6% of strategy
                confidence=0.75,
                rationale="AI content generation reducing demand for traditional journalism and content creation"
            ),
            Position(
                symbol="NYT",  # New York Times - Traditional media
                side="short",
                weight=0.04,  # 4% of strategy
                confidence=0.70,
                rationale="AI-powered news aggregation and generation threatening subscription-based news model"
            )
        ]
    
    def calculate_trade_orders(self, allocation: PortfolioAllocation) -> List[Dict]:
        """
        Calculate specific buy/sell orders based on user's portfolio allocation
        
        Args:
            allocation: User's allocation to this strategy
            
        Returns:
            List of trade orders with symbol, side, quantity, and dollar amount
        """
        orders = []
        
        # Get current market prices (mock or real)
        symbols = [pos.symbol for pos in self.positions]
        quotes = self._get_current_quotes(symbols)
        
        for position in self.positions:
            # Calculate dollar amount for this position
            position_amount = allocation.allocated_amount * position.weight
            
            # Get current price
            current_price = quotes.get(position.symbol, {}).get('price', 0)
            if current_price == 0:
                continue
                
            # Calculate quantity (supporting fractional shares)
            if position.side == 'long':
                quantity = position_amount / current_price
                side = 'buy'
            else:  # short
                quantity = position_amount / current_price
                side = 'sell'
            
            order = {
                'symbol': position.symbol,
                'side': side,
                'quantity': round(quantity, 6),  # Alpaca supports up to 6 decimal places
                'dollar_amount': position_amount,
                'current_price': current_price,
                'weight': position.weight,
                'confidence': position.confidence,
                'rationale': position.rationale,
                'order_type': 'market',  # Start with market orders for simplicity
                'time_in_force': 'day'
            }
            
            orders.append(order)
        
        return orders
    
    def _get_current_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current market quotes for given symbols"""
        quotes = {}
        
        # For now, use mock prices (in real implementation, this would call Alpaca API)
        for symbol in symbols:
            if symbol in self.mock_prices:
                # Add some random variation to simulate market movement
                import random
                base_price = self.mock_prices[symbol]
                variation = random.uniform(-0.02, 0.02)  # ±2% variation
                current_price = base_price * (1 + variation)
                
                quotes[symbol] = {
                    'price': current_price,
                    'bid': current_price * 0.999,
                    'ask': current_price * 1.001,
                    'timestamp': datetime.now().isoformat()
                }
        
        return quotes
    
    def execute_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        Execute trade orders (simplified version for demo)
        
        Args:
            orders: List of trade orders to execute
            
        Returns:
            List of order execution results
        """
        results = []
        
        for order in orders:
            # Simulate order execution
            result = {
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['quantity'],
                'dollar_amount': order['dollar_amount'],
                'status': 'simulated',
                'order_id': f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{order['symbol']}",
                'submitted_at': datetime.now().isoformat(),
                'rationale': order['rationale']
            }
            
            results.append(result)
            print(f"✅ Order simulated: {order['side']} {order['quantity']} {order['symbol']} (${order['dollar_amount']:.2f})")
        
        return results
    
    def get_portfolio_performance(self, allocation: PortfolioAllocation) -> Dict:
        """
        Calculate current portfolio performance for this strategy allocation (simplified)
        
        Args:
            allocation: User's allocation to this strategy
            
        Returns:
            Performance metrics including P&L, returns, and position details
        """
        # Simulate some performance data
        import random
        
        # Generate mock positions with some random performance
        strategy_positions = []
        total_market_value = 0
        total_unrealized_pl = 0
        
        for position in self.positions:
            position_amount = allocation.allocated_amount * position.weight
            current_price = self.mock_prices.get(position.symbol, 100)
            
            # Simulate some performance (random between -10% and +15%)
            performance = random.uniform(-0.10, 0.15)
            market_value = position_amount * (1 + performance)
            unrealized_pl = market_value - position_amount
            
            pos_data = {
                'symbol': position.symbol,
                'quantity': position_amount / current_price,
                'market_value': market_value,
                'avg_entry_price': current_price,
                'current_price': current_price * (1 + performance),
                'unrealized_pl': unrealized_pl,
                'unrealized_plpc': performance,
                'side': position.side
            }
            
            strategy_positions.append(pos_data)
            total_market_value += market_value
            total_unrealized_pl += unrealized_pl
        
        # Calculate overall performance
        total_return_pct = (total_unrealized_pl / allocation.allocated_amount * 100) if allocation.allocated_amount > 0 else 0
        
        performance = {
            'strategy_name': self.strategy_name,
            'allocated_amount': allocation.allocated_amount,
            'current_market_value': total_market_value,
            'unrealized_pl': total_unrealized_pl,
            'total_return_pct': total_return_pct,
            'positions': strategy_positions,
            'last_updated': datetime.now().isoformat(),
            'account_buying_power': 100000.0,  # Mock data
            'account_portfolio_value': 100000.0  # Mock data
        }
        
        return performance
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of the current strategy positions and logic"""
        long_positions = [pos for pos in self.positions if pos.side == 'long']
        short_positions = [pos for pos in self.positions if pos.side == 'short']
        
        return {
            'strategy_name': self.strategy_name,
            'description': 'AI-driven long/short equity strategy focusing on technology disruption',
            'last_updated': self.last_updated.isoformat(),
            'total_positions': len(self.positions),
            'long_positions': len(long_positions),
            'short_positions': len(short_positions),
            'long_weight': sum(pos.weight for pos in long_positions),
            'short_weight': sum(pos.weight for pos in short_positions),
            'avg_confidence': sum(pos.confidence for pos in self.positions) / len(self.positions),
            'positions': [
                {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'weight': pos.weight,
                    'confidence': pos.confidence,
                    'rationale': pos.rationale
                }
                for pos in self.positions
            ]
        }


def main():
    """Test the strategy with sample data"""
    # Initialize strategy in demo mode
    strategy = AILongShortStrategy()
    
    # Create sample allocation
    allocation = PortfolioAllocation(
        user_id="test_user_001",
        strategy_name="AI Long/Short",
        allocation_percentage=60.0,  # 60% of portfolio
        total_portfolio_value=100000.0,  # $100k portfolio
        allocated_amount=60000.0  # $60k to this strategy
    )
    
    # Get strategy summary
    summary = strategy.get_strategy_summary()
    print("=== AI Long/Short Strategy Summary ===")
    print(json.dumps(summary, indent=2))
    
    # Calculate trade orders
    orders = strategy.calculate_trade_orders(allocation)
    print("\n=== Calculated Trade Orders ===")
    for order in orders:
        print(f"{order['side'].upper()} ${order['dollar_amount']:.2f} {order['symbol']} "
              f"({order['quantity']:.6f} shares) - {order['rationale']}")
    
    # Simulate order execution
    results = strategy.execute_orders(orders)
    print("\n=== Order Execution Results ===")
    print(json.dumps(results, indent=2))
    
    # Get performance
    performance = strategy.get_portfolio_performance(allocation)
    print("\n=== Portfolio Performance ===")
    print(json.dumps(performance, indent=2))


if __name__ == "__main__":
    main()

