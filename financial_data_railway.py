"""
Financial data module for Railway deployment
Uses direct HTTP requests to Yahoo Finance (no Manus API dependency)
"""

import requests
import json
from datetime import datetime


def get_stock_data(ticker):
    """
    Get stock data using direct Yahoo Finance API calls
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock data including price, chart, and financials
    """
    try:
        # Yahoo Finance API endpoints (public, no auth required)
        base_url = "https://query1.finance.yahoo.com/v8/finance"
        
        # Get chart data (6 months)
        chart_url = f"{base_url}/chart/{ticker}"
        chart_params = {
            'region': 'US',
            'interval': '1d',
            'range': '6mo',
            'includeAdjustedClose': 'true'
        }
        
        chart_response = requests.get(chart_url, params=chart_params, timeout=10)
        chart_data_raw = chart_response.json()
        
        if not chart_data_raw or 'chart' not in chart_data_raw:
            return get_fallback_data(ticker)
        
        if 'error' in chart_data_raw['chart']:
            return get_fallback_data(ticker)
        
        result = chart_data_raw['chart']['result'][0]
        meta = result['meta']
        
        # Extract price data
        timestamps = result.get('timestamp', [])
        quotes = result.get('indicators', {}).get('quote', [{}])[0]
        
        # Calculate 6-month return
        close_prices = [p for p in quotes.get('close', []) if p is not None]
        six_month_return = 0.0
        if len(close_prices) >= 2:
            six_month_return = ((close_prices[-1] - close_prices[0]) / close_prices[0]) * 100
        
        # Format chart data
        chart_data = []
        for i, timestamp in enumerate(timestamps):
            if i < len(quotes.get('close', [])) and quotes['close'][i] is not None:
                chart_data.append({
                    'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
                    'price': round(quotes['close'][i], 2)
                })
        
        # Build response
        stock_data = {
            'ticker': ticker,
            'name': meta.get('longName', meta.get('shortName', ticker)),
            'currentPrice': meta.get('regularMarketPrice', 0),
            'marketCap': format_market_cap(meta.get('marketCap', 0)),
            'sixMonthReturn': round(six_month_return, 2),
            'chartData': chart_data,
            'pe': meta.get('trailingPE', None),
            'ps': meta.get('priceToSalesTrailing12Months', None),
            'pb': meta.get('priceToBook', None),
            'evEbitda': None,  # Not available in basic endpoint
            'fiftyTwoWeekHigh': meta.get('fiftyTwoWeekHigh', None),
            'fiftyTwoWeekLow': meta.get('fiftyTwoWeekLow', None),
            'volume': meta.get('regularMarketVolume', 0),
            'valuation': None,
            'outlook': None,
            'companyMetrics': None,
            'analystReport': None,
            'news': None
        }
        
        return stock_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return get_fallback_data(ticker)


def format_market_cap(market_cap):
    """Format market cap to human-readable string"""
    if not market_cap or market_cap == 0:
        return "N/A"
    
    if market_cap >= 1_000_000_000_000:  # Trillion
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000_000:  # Billion
        return f"${market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:  # Million
        return f"${market_cap / 1_000_000:.2f}M"
    else:
        return f"${market_cap:,.0f}"


def get_fallback_data(ticker):
    """Return fallback data when API fails"""
    return {
        'ticker': ticker,
        'name': ticker,
        'currentPrice': 0,
        'marketCap': "N/A",
        'sixMonthReturn': 0.0,
        'chartData': [],
        'pe': None,
        'ps': None,
        'pb': None,
        'evEbitda': None,
        'fiftyTwoWeekHigh': None,
        'fiftyTwoWeekLow': None,
        'volume': 0,
        'valuation': None,
        'outlook': None,
        'companyMetrics': None,
        'analystReport': None,
        'news': None,
        'error': 'Data temporarily unavailable'
    }


# Test function
if __name__ == "__main__":
    print("Testing Railway-compatible financial data module...")
    print("=" * 80)
    
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in test_tickers:
        print(f"\nFetching {ticker}...")
        data = get_stock_data(ticker)
        print(f"  Price: ${data['currentPrice']}")
        print(f"  Market Cap: {data['marketCap']}")
        print(f"  6M Return: {data['sixMonthReturn']}%")
        print(f"  Chart Data Points: {len(data['chartData'])}")
        print(f"  P/E: {data['pe']}")

