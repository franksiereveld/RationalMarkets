"""
AI Long/Short Investment Strategy MVP

This module implements a unified global AI-driven long/short equity strategy
accessible through both Alpaca and Swissquote APIs for worldwide users.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import alpaca_trade_api as tradeapi
from dataclasses import dataclass
from global_strategy import GlobalAILongShortStrategy


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
    AI Long/Short Strategy Implementation
    
    This strategy uses a unified global approach accessible to users worldwide
    through appropriate broker APIs (Alpaca for US, Swissquote for Europe).
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None, broker_type: str = 'alpaca'):
        """Initialize strategy with broker API credentials"""
        self.broker_type = broker_type
        self.api = None
        
        if api_key and secret_key:
            if broker_type == 'alpaca':
                self.api = tradeapi.REST(api_key, secret_key, base_url or 'https://paper-api.alpaca.markets', api_version='v2')
            elif broker_type == 'swissquote':
                # Import Swissquote API if available
                try:
                    from swissquote_api import SwissquoteAPI
                    self.api = SwissquoteAPI(api_key, secret_key)
                except ImportError:
                    print("Swissquote API not available, running in demo mode")
        
        # Initialize global strategy
        self.global_strategy = GlobalAILongShortStrategy(self.api)
        self.strategy_name = self.global_strategy.strategy_name
        self.last_updated = datetime.now()
        # Get positions from global strategy
        self.positions = self._convert_global_positions()
    
    def _convert_global_positions(self) -> List[Position]:
        """Convert global strategy positions to legacy Position format for compatibility"""
        positions = []
        
        # Convert long positions
        for pos in self.global_strategy.long_positions:
            positions.append(Position(
                symbol=self.global_strategy.get_broker_symbol(pos, self.broker_type),
                side="long",
                weight=pos['target_allocation'] * 0.6,  # 60% allocation to longs
                confidence=pos['confidence'] / 100.0,  # Convert to 0-1 scale
                rationale=pos['rationale']
            ))
        
        # Convert short positions
        for pos in self.global_strategy.short_positions:
            positions.append(Position(
                symbol=self.global_strategy.get_broker_symbol(pos, self.broker_type),
                side="short",
                weight=pos['target_allocation'] * 0.4,  # 40% allocation to shorts
                confidence=pos['confidence'] / 100.0,  # Convert to 0-1 scale
                rationale=pos['rationale']
            ))
        
        return positions
    
    def calculate_trade_orders(self, allocation: PortfolioAllocation) -> List[Dict]:
        """
        Calculate specific buy/sell orders based on user's portfolio allocation
        Uses the global strategy for unified worldwide approach
        
        Args:
            allocation: User's allocation to this strategy
            
        Returns:
            List of trade orders with symbol, side, quantity, and dollar amount
        """
        # Use global strategy to calculate orders
        orders = self.global_strategy.calculate_trade_orders(
            portfolio_value=allocation.total_portfolio_value,
            allocation_percentage=allocation.allocation_percentage,
            broker_type=self.broker_type
        )
        
        # Convert to legacy format for compatibility
        legacy_orders = []
        for order in orders:
            legacy_order = {
                'symbol': order['symbol'],
                'side': order['side'].lower(),
                'quantity': order['quantity'],
                'dollar_amount': order['estimated_value'],
                'current_price': order['estimated_price'],
                'weight': order['allocation_pct'] / 100.0,
                'confidence': order['confidence'] / 100.0,
                'rationale': order['rationale'],
                'order_type': 'market',
                'time_in_force': 'day',
                'currency': order['currency'],
                'market': order['market']
            }
            legacy_orders.append(legacy_order)
        
        return legacy_orders
    
    def _get_current_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current market quotes for given symbols"""
        quotes = {}
        
        try:
            # Get latest quotes from Alpaca
            latest_quotes = self.api.get_latest_quotes(symbols)
            
            for symbol in symbols:
                if symbol in latest_quotes:
                    quote = latest_quotes[symbol]
                    quotes[symbol] = {
                        'price': (quote.ask_price + quote.bid_price) / 2,  # Mid price
                        'bid': quote.bid_price,
                        'ask': quote.ask_price,
                        'timestamp': quote.timestamp
                    }
        except Exception as e:
            print(f"Error fetching quotes: {e}")
            # Fallback to last trade prices
            try:
                latest_trades = self.api.get_latest_trades(symbols)
                for symbol in symbols:
                    if symbol in latest_trades:
                        trade = latest_trades[symbol]
                        quotes[symbol] = {
                            'price': trade.price,
                            'bid': trade.price,
                            'ask': trade.price,
                            'timestamp': trade.timestamp
                        }
            except Exception as e2:
                print(f"Error fetching trades: {e2}")
        
        return quotes
    
    def execute_orders(self, orders: List[Dict]) -> List[Dict]:
        """
        Execute trade orders through broker API
        Uses global strategy for unified execution
        
        Args:
            orders: List of trade orders to execute
            
        Returns:
            List of order execution results
        """
        # Convert legacy orders back to global strategy format
        global_orders = []
        for order in orders:
            global_order = {
                'symbol': order['symbol'],
                'side': order['side'].upper(),
                'quantity': order['quantity'],
                'estimated_price': order['current_price'],
                'estimated_value': order['dollar_amount'],
                'rationale': order['rationale']
            }
            global_orders.append(global_order)
        
        # Execute through global strategy
        results = self.global_strategy.execute_orders(global_orders)
        
        # Convert results to legacy format
        legacy_results = []
        for result in results:
            legacy_result = {
                'symbol': result['symbol'],
                'side': result['side'].lower(),
                'quantity': result['quantity'],
                'dollar_amount': result.get('estimated_value', 0),
                'status': result['status'].lower(),
                'order_id': result['order_id'],
                'submitted_at': result.get('submitted_at'),
                'error': result.get('message') if result['status'] == 'FAILED' else None,
                'rationale': global_orders[legacy_results.__len__()]['rationale'] if legacy_results.__len__() < len(global_orders) else ''
            }
            legacy_results.append(legacy_result)
            
            # Print status
            if result['status'] in ['SUBMITTED', 'SIMULATED']:
                print(f"✅ Order {result['status'].lower()}: {result['side']} {result['quantity']} {result['symbol']}")
            else:
                print(f"❌ Order failed: {result['side']} {result['quantity']} {result['symbol']} - {result.get('message', 'Unknown error')}")
        
        return legacy_results
    
    def get_portfolio_performance(self, allocation: PortfolioAllocation) -> Dict:
        """
        Calculate current portfolio performance for this strategy allocation
        
        Args:
            allocation: User's allocation to this strategy
            
        Returns:
            Performance metrics including P&L, returns, and position details
        """
        try:
            # Get current account info
            account = self.api.get_account()
            
            # Get current positions
            positions = self.api.list_positions()
            
            # Calculate strategy-specific performance
            strategy_positions = []
            total_market_value = 0
            total_unrealized_pl = 0
            
            strategy_symbols = {pos.symbol for pos in self.positions}
            
            for position in positions:
                if position.symbol in strategy_symbols:
                    pos_data = {
                        'symbol': position.symbol,
                        'quantity': float(position.qty),
                        'market_value': float(position.market_value),
                        'avg_entry_price': float(position.avg_entry_price),
                        'current_price': float(position.current_price),
                        'unrealized_pl': float(position.unrealized_pl),
                        'unrealized_plpc': float(position.unrealized_plpc),
                        'side': 'long' if float(position.qty) > 0 else 'short'
                    }
                    
                    strategy_positions.append(pos_data)
                    total_market_value += pos_data['market_value']
                    total_unrealized_pl += pos_data['unrealized_pl']
            
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
                'account_buying_power': float(account.buying_power),
                'account_portfolio_value': float(account.portfolio_value)
            }
            
            return performance
            
        except Exception as e:
            print(f"Error calculating performance: {e}")
            return {
                'strategy_name': self.strategy_name,
                'allocated_amount': allocation.allocated_amount,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of the current strategy positions and logic"""
        return self.global_strategy.get_strategy_summary()


def main():
    """Test the strategy with sample data for both brokers"""
    import sys
    
    # Determine broker type from command line or environment
    broker_type = sys.argv[1] if len(sys.argv) > 1 else os.getenv('BROKER_TYPE', 'alpaca')
    
    if broker_type == 'alpaca':
        # Alpaca configuration
        api_key = os.getenv('ALPACA_API_KEY', 'your_paper_api_key')
        secret_key = os.getenv('ALPACA_SECRET_KEY', 'your_paper_secret_key')
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        print(f"Testing with Alpaca (Demo Mode: {not api_key or api_key == 'your_paper_api_key'})")
    elif broker_type == 'swissquote':
        # Swissquote configuration
        api_key = os.getenv('SWISSQUOTE_API_KEY', 'your_swissquote_key')
        secret_key = os.getenv('SWISSQUOTE_SECRET_KEY', 'your_swissquote_secret')
        base_url = None
        print(f"Testing with Swissquote (Demo Mode: {not api_key or api_key == 'your_swissquote_key'})")
    else:
        print(f"Unknown broker type: {broker_type}")
        return
    
    # Initialize strategy
    strategy = AILongShortStrategy(api_key, secret_key, base_url, broker_type)
    
    # Create sample allocation
    allocation = PortfolioAllocation(
        user_id="test_user_001",
        strategy_name="Global AI Long/Short",
        allocation_percentage=60.0,  # 60% of portfolio
        total_portfolio_value=100000.0,  # $100k portfolio
        allocated_amount=60000.0  # $60k to this strategy
    )
    
    # Get strategy summary
    summary = strategy.get_strategy_summary()
    print(f"\n=== {summary['name']} Summary ===")
    print(f"Description: {summary['description']}")
    print(f"Total Positions: {summary['total_positions']} ({summary['long_positions']} long, {summary['short_positions']} short)")
    print(f"Geographic Scope: {summary['geographic_scope']}")
    print(f"Markets: {', '.join(summary['markets'])}")
    print(f"Currencies: {', '.join(summary['currencies'])}")
    print(f"Average Confidence: {summary['avg_confidence']:.1f}%")
    
    # Calculate trade orders
    orders = strategy.calculate_trade_orders(allocation)
    print(f"\n=== Calculated Trade Orders ({broker_type.title()}) ===")
    total_long = sum(order['dollar_amount'] for order in orders if order['side'] == 'buy')
    total_short = sum(order['dollar_amount'] for order in orders if order['side'] == 'sell')
    
    print(f"Total Long Allocation: ${total_long:,.2f}")
    print(f"Total Short Allocation: ${total_short:,.2f}")
    print(f"Total Strategy Allocation: ${total_long + total_short:,.2f}")
    print()
    
    for order in orders:
        currency = order.get('currency', 'USD')
        market = order.get('market', 'US')
        print(f"{order['side'].upper()} {order['quantity']:.6f} {order['symbol']} @ {currency} {order['current_price']:.2f}")
        print(f"  Value: {currency} {order['dollar_amount']:,.2f} | Market: {market} | Confidence: {order['confidence']*100:.0f}%")
        print(f"  Rationale: {order['rationale']}")
        print()
    
    # Test order execution in demo mode
    print("=== Testing Order Execution (Demo Mode) ===")
    results = strategy.execute_orders(orders)
    
    successful = sum(1 for r in results if r['status'] in ['submitted', 'simulated'])
    failed = len(results) - successful
    
    print(f"\nExecution Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {successful/len(results)*100:.1f}%")


if __name__ == "__main__":
    main()

