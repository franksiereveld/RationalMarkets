"""
Portfolio Metrics Calculation Module
Calculates trade-level KPIs from individual positions
"""

def calculate_portfolio_beta(positions):
    """
    Calculate weighted average beta for the portfolio
    
    Args:
        positions: List of all positions (longs + shorts + derivatives)
        Each position has: allocation (e.g., "25%" or "-15%"), beta
    
    Returns:
        float: Portfolio beta
    """
    total_beta = 0.0
    
    for position in positions:
        # Parse allocation (remove % sign, convert to decimal)
        allocation_str = position.get('allocation', '0%').replace('%', '')
        try:
            weight = abs(float(allocation_str) / 100.0)  # Use absolute value for shorts
        except ValueError:
            continue
        
        # Get position beta (default to 1.0 if not available)
        beta = position.get('beta')
        if beta is None or beta == 'N/A':
            beta = 1.0
        
        try:
            beta = float(beta)
        except (ValueError, TypeError):
            beta = 1.0
        
        # Weighted contribution
        total_beta += weight * beta
    
    return round(total_beta, 2)


def calculate_net_exposure(longs, shorts):
    """
    Calculate net long/short exposure
    
    Args:
        longs: List of long positions with allocation
        shorts: List of short positions with allocation (negative %)
    
    Returns:
        dict: {
            'long_exposure': float,
            'short_exposure': float,
            'net_exposure': float,
            'gross_exposure': float
        }
    """
    # Sum long allocations
    long_exposure = 0.0
    for position in longs:
        allocation_str = position.get('allocation', '0%').replace('%', '')
        try:
            long_exposure += float(allocation_str)
        except ValueError:
            continue
    
    # Sum short allocations (already negative)
    short_exposure = 0.0
    for position in shorts:
        allocation_str = position.get('allocation', '0%').replace('%', '')
        try:
            short_exposure += float(allocation_str)  # e.g., -15%, -20% → -35%
        except ValueError:
            continue
    
    # Net exposure
    net_exposure = long_exposure + short_exposure
    
    # Gross exposure (total capital deployed)
    gross_exposure = long_exposure + abs(short_exposure)
    
    return {
        'long_exposure': round(long_exposure, 1),      # e.g., 100.0
        'short_exposure': round(short_exposure, 1),    # e.g., -35.0
        'net_exposure': round(net_exposure, 1),        # e.g., 65.0
        'gross_exposure': round(gross_exposure, 1)     # e.g., 135.0
    }


def calculate_investment_breakdown(exposure_dict, investment_amount=1000):
    """
    Calculate dollar amounts for a hypothetical investment
    
    Args:
        exposure_dict: Output from calculate_net_exposure()
        investment_amount: Dollar amount (default $1000)
    
    Returns:
        dict: Dollar amounts for long, short, net positions
    """
    long_dollars = (exposure_dict['long_exposure'] / 100) * investment_amount
    short_dollars = (abs(exposure_dict['short_exposure']) / 100) * investment_amount
    net_dollars = (exposure_dict['net_exposure'] / 100) * investment_amount
    
    return {
        'long_dollars': round(long_dollars, 2),      # e.g., $1000.00
        'short_dollars': round(short_dollars, 2),    # e.g., $350.00
        'net_dollars': round(net_dollars, 2),        # e.g., $650.00
        'total_capital_required': round(long_dollars + short_dollars, 2)  # e.g., $1350.00
    }


def calculate_portfolio_metrics(analysis):
    """
    Calculate all portfolio-level metrics
    
    Args:
        analysis: Complete trade analysis from AI
    
    Returns:
        dict: Portfolio metrics including beta, exposures, investment breakdown
    """
    all_positions = (
        analysis.get('longs', []) + 
        analysis.get('shorts', []) + 
        analysis.get('derivatives', [])
    )
    
    # Calculate beta
    portfolio_beta = calculate_portfolio_beta(all_positions)
    
    # Calculate exposures
    exposure = calculate_net_exposure(
        analysis.get('longs', []),
        analysis.get('shorts', [])
    )
    
    # Calculate investment breakdown for $1000
    investment = calculate_investment_breakdown(exposure, 1000)
    
    return {
        'portfolio_beta': portfolio_beta,
        'alpha': analysis.get('alpha', 0),  # From AI
        'sentiment': analysis.get('sentiment', 'NEUTRAL'),  # From AI
        'risk_level': analysis.get('riskLevel', 'MODERATE'),  # From AI
        **exposure,
        **investment
    }


# Test function
if __name__ == "__main__":
    # Test with example trade
    test_analysis = {
        'longs': [
            {'ticker': 'AAPL', 'allocation': '40%', 'beta': 1.2},
            {'ticker': 'MSFT', 'allocation': '35%', 'beta': 0.9},
            {'ticker': 'GOOGL', 'allocation': '25%', 'beta': 1.1}
        ],
        'shorts': [
            {'ticker': 'TSLA', 'allocation': '-15%', 'beta': 2.0},
            {'ticker': 'NVDA', 'allocation': '-20%', 'beta': 1.8}
        ],
        'alpha': 2.5,
        'sentiment': 'BULLISH',
        'riskLevel': 'MODERATE'
    }
    
    metrics = calculate_portfolio_metrics(test_analysis)
    
    print("Portfolio Metrics:")
    print(f"  Portfolio Beta: {metrics['portfolio_beta']}")
    print(f"  Alpha: {metrics['alpha']}%")
    print(f"  Sentiment: {metrics['sentiment']}")
    print(f"  Risk Level: {metrics['risk_level']}")
    print(f"\nExposure:")
    print(f"  Long: {metrics['long_exposure']}%")
    print(f"  Short: {metrics['short_exposure']}%")
    print(f"  Net: {metrics['net_exposure']}%")
    print(f"  Gross: {metrics['gross_exposure']}%")
    print(f"\nFor $1000 Investment:")
    print(f"  Long positions: ${metrics['long_dollars']}")
    print(f"  Short positions: ${metrics['short_dollars']}")
    print(f"  Net exposure: ${metrics['net_dollars']}")
    print(f"  Total capital required: ${metrics['total_capital_required']}")

