#!/usr/bin/env python3
"""
Financial Data API for RationalMarkets
Fetches real stock prices, multiples, and historical data using yfinance
"""

import yfinance as yf
from datetime import datetime, timedelta

def get_stock_data(symbol):
    """
    Fetch comprehensive stock data for a given symbol
    
    Returns:
        dict: Stock data including price, multiples, and chart data
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get historical data for 6-month chart
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        hist = stock.history(start=start_date, end=end_date)
        
        # Calculate price change
        if len(hist) > 0:
            first_price = hist['Close'].iloc[0]
            last_price = hist['Close'].iloc[-1]
            price_change = ((last_price - first_price) / first_price) * 100
        else:
            price_change = 0
        
        # Extract financial multiples
        pe_ratio = info.get('trailingPE', None) or info.get('forwardPE', None)
        ps_ratio = info.get('priceToSalesTrailing12Months', None)
        pb_ratio = info.get('priceToBook', None)
        ev_ebitda = info.get('enterpriseToEbitda', None)
        
        # Get current price and market cap
        current_price = info.get('currentPrice', None) or info.get('regularMarketPrice', None)
        market_cap = info.get('marketCap', None)
        
        # Format market cap
        if market_cap:
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
        else:
            market_cap_str = "N/A"
        
        # Prepare chart data (simplified for frontend)
        chart_data = []
        if len(hist) > 0:
            # Sample 50 points for chart
            sample_size = min(50, len(hist))
            step = max(1, len(hist) // sample_size)
            for i in range(0, len(hist), step):
                chart_data.append({
                    'date': hist.index[i].strftime('%Y-%m-%d'),
                    'price': float(hist['Close'].iloc[i])
                })
        
        return {
            'symbol': symbol.upper(),
            'currentPrice': round(current_price, 2) if current_price else 0,
            'priceChange': round(price_change, 2),
            'marketCap': market_cap_str,
            'multiples': {
                'pe': round(pe_ratio, 1) if pe_ratio else None,
                'ps': round(ps_ratio, 1) if ps_ratio else None,
                'pb': round(pb_ratio, 1) if pb_ratio else None,
                'evEbitda': round(ev_ebitda, 1) if ev_ebitda else None
            },
            'chartData': chart_data,
            'success': True
        }
    
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return {
            'symbol': symbol.upper(),
            'currentPrice': 0,
            'priceChange': 0,
            'marketCap': 'N/A',
            'multiples': {
                'pe': None,
                'ps': None,
                'pb': None,
                'evEbitda': None
            },
            'chartData': [],
            'success': False,
            'error': str(e)
        }


def get_multiple_stocks_data(symbols):
    """
    Fetch data for multiple stock symbols
    
    Args:
        symbols: List of stock ticker symbols
    
    Returns:
        dict: Dictionary mapping symbols to their data
    """
    results = {}
    for symbol in symbols:
        results[symbol.upper()] = get_stock_data(symbol)
    return results


if __name__ == '__main__':
    # Test with some symbols
    test_symbols = ['NVDA', 'TSLA', 'INTC', 'CSCO']
    
    print("Testing Financial Data API...")
    print("=" * 80)
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        data = get_stock_data(symbol)
        
        if data['success']:
            print(f"  Current Price: ${data['currentPrice']}")
            print(f"  Price Change (6M): {data['priceChange']:+.2f}%")
            print(f"  Market Cap: {data['marketCap']}")
            print(f"  P/E: {data['multiples']['pe']}")
            print(f"  P/S: {data['multiples']['ps']}")
            print(f"  P/B: {data['multiples']['pb']}")
            print(f"  EV/EBITDA: {data['multiples']['evEbitda']}")
            print(f"  Chart Data Points: {len(data['chartData'])}")
        else:
            print(f"  Error: {data.get('error', 'Unknown error')}")

