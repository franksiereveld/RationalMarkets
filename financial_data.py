"""
Financial data module using Manus API Hub
Provides reliable stock data without external dependencies
"""

import sys
import json
from datetime import datetime

# Add Manus API client path
sys.path.append('/opt/.manus/.sandbox-runtime')

try:
    from data_api import ApiClient
    MANUS_API_AVAILABLE = True
except ImportError:
    MANUS_API_AVAILABLE = False
    print("Warning: Manus API not available, using fallback mode")


def get_stock_data(ticker):
    """
    Get comprehensive stock data for a single ticker
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock data including price, financials, and chart data
    """
    if not MANUS_API_AVAILABLE:
        return get_fallback_data(ticker)
    
    try:
        client = ApiClient()
        
        # Get stock chart data (includes price and historical data)
        response = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': ticker,
            'region': 'US',
            'interval': '1d',
            'range': '6mo',  # 6 months of data for charts
            'includeAdjustedClose': True
        })
        
        if not response or 'chart' not in response or 'result' not in response['chart']:
            return get_fallback_data(ticker)
        
        result = response['chart']['result'][0]
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
            'marketCap': meta.get('marketCap', 0),
            'sixMonthReturn': round(six_month_return, 2),
            'chartData': chart_data,
            'financialData': {
                'currentPrice': meta.get('regularMarketPrice', 0),
                'marketCap': format_market_cap(meta.get('marketCap', meta.get('regularMarketCap', 0))),
                'pe': meta.get('trailingPE', None),
                'ps': meta.get('priceToSalesTrailing12Months', None),
                'pb': meta.get('priceToBook', None),
                'evEbitda': meta.get('enterpriseToEbitda', None),
                'fiftyTwoWeekHigh': meta.get('fiftyTwoWeekHigh', None),
                'fiftyTwoWeekLow': meta.get('fiftyTwoWeekLow', None),
                'volume': meta.get('regularMarketVolume', 0)
            }
        }
        
        return stock_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return get_fallback_data(ticker)


def get_multiple_stocks_data(tickers):
    """
    Get stock data for multiple tickers
    
    Args:
        tickers (list): List of stock ticker symbols
        
    Returns:
        dict: Dictionary mapping tickers to their stock data
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_stock_data(ticker)
    return results


def format_market_cap(market_cap):
    """Format market cap in billions or trillions"""
    if market_cap == 0:
        return "N/A"
    elif market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.2f}M"
    else:
        return f"${market_cap:,.0f}"


def get_fallback_data(ticker):
    """
    Provide fallback data structure when API is unavailable
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Minimal stock data structure
    """
    return {
        'ticker': ticker,
        'name': ticker,
        'currentPrice': 0,
        'marketCap': 0,
        'sixMonthReturn': 0.0,
        'chartData': [],
        'financialData': {
            'currentPrice': 0,
            'marketCap': 'N/A',
            'pe': None,
            'ps': None,
            'pb': None,
            'evEbitda': None,
            'fiftyTwoWeekHigh': None,
            'fiftyTwoWeekLow': None,
            'volume': 0
        },
        'error': 'Data temporarily unavailable'
    }


# Test function
if __name__ == "__main__":
    print("Testing financial data module...")
    
    # Test single stock
    print("\nTesting single stock (AAPL):")
    aapl_data = get_stock_data("AAPL")
    print(f"Ticker: {aapl_data['ticker']}")
    print(f"Name: {aapl_data['name']}")
    print(f"Current Price: ${aapl_data['currentPrice']}")
    print(f"Market Cap: {aapl_data['financialData']['marketCap']}")
    print(f"6M Return: {aapl_data['sixMonthReturn']}%")
    print(f"Chart data points: {len(aapl_data['chartData'])}")
    
    # Test multiple stocks
    print("\nTesting multiple stocks:")
    tickers = ["MSFT", "GOOGL", "NVDA"]
    multi_data = get_multiple_stocks_data(tickers)
    for ticker, data in multi_data.items():
        print(f"{ticker}: ${data['currentPrice']} ({data['sixMonthReturn']}% 6M return)")
