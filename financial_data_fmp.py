"""
Production-ready financial data module using FMP Stable API
Works with FMP API key for real-time stock data
"""

import os
import requests
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FMP Configuration
FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
FMP_BASE_URL = 'https://financialmodelingprep.com/stable'

if not FMP_API_KEY:
    logger.warning("FMP_API_KEY not set in environment variables")


def get_stock_data(ticker):
    """
    Get comprehensive stock data for a single ticker using FMP Stable API
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock data including price, company info, and market data
    """
    try:
        logger.info(f"Fetching data for {ticker} from FMP API")
        logger.info(f"FMP_API_KEY present: {bool(FMP_API_KEY)}")
        logger.info(f"FMP_API_KEY length: {len(FMP_API_KEY) if FMP_API_KEY else 0}")
        
        stock_data = {
            'ticker': ticker,
            'name': ticker,
            'currentPrice': 0,
            'priceChange': 0,
            'priceChangePercent': 0,
            'previousClose': 0,
            'marketCap': 'N/A',
            'sixMonthReturn': 0.0,
            'chartData': [],
            'pe': None,
            'ps': None,
            'pb': None,
            'beta': None,
            'evEbitda': None,
            'fiftyTwoWeekHigh': None,
            'fiftyTwoWeekLow': None,
            'volume': 0,
            'averageVolume': None,
            'dividendYield': None,
            'lastDividend': None,
            'sector': None,
            'industry': None,
            'country': None,
            'exchange': None,
            'description': None,
            'ceo': None,
            'website': None,
            'image': None,
            'targetMeanPrice': None,
            'recommendationKey': None,
            'numberOfAnalystOpinions': None,
            'news': None
        }
        
        # 1. Get Quote (price, volume, market cap)
        quote_url = f"{FMP_BASE_URL}/quote?symbol={ticker}&apikey={FMP_API_KEY}"
        logger.info(f"Requesting: {FMP_BASE_URL}/quote?symbol={ticker}&apikey=***")
        quote_response = requests.get(quote_url, timeout=10)
        logger.info(f"Response status: {quote_response.status_code}")
        quote_response.raise_for_status()
        quote_data = quote_response.json()
        logger.info(f"Quote data keys: {list(quote_data.keys()) if isinstance(quote_data, dict) else 'list'}")
        
        # Check for API error
        if isinstance(quote_data, dict) and 'Error Message' in quote_data:
            logger.error(f"FMP API Error: {quote_data['Error Message']}")
            return get_fallback_data(ticker)
        
        if quote_data and len(quote_data) > 0:
            quote = quote_data[0]
            stock_data['currentPrice'] = quote.get('price', 0)
            stock_data['priceChange'] = quote.get('change', 0)
            stock_data['priceChangePercent'] = quote.get('changePercentage', 0)
            stock_data['previousClose'] = quote.get('previousClose', 0)
            stock_data['name'] = quote.get('name', ticker)
            stock_data['volume'] = quote.get('volume', 0)
            stock_data['averageVolume'] = quote.get('avgVolume', quote.get('averageVolume'))
            stock_data['fiftyTwoWeekHigh'] = quote.get('yearHigh')
            stock_data['fiftyTwoWeekLow'] = quote.get('yearLow')
            stock_data['exchange'] = quote.get('exchange')
            stock_data['pe'] = quote.get('pe')  # Extract P/E ratio from quote
            
            # Format market cap
            market_cap = quote.get('marketCap', 0)
            if market_cap >= 1_000_000_000_000:
                stock_data['marketCap'] = f"${market_cap / 1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                stock_data['marketCap'] = f"${market_cap / 1_000_000_000:.2f}B"
            elif market_cap > 0:
                stock_data['marketCap'] = f"${market_cap / 1_000_000:.2f}M"
        
        # 2. Get Profile (company info, sector, industry)
        profile_url = f"{FMP_BASE_URL}/profile?symbol={ticker}&apikey={FMP_API_KEY}"
        profile_response = requests.get(profile_url, timeout=10)
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        
        if profile_data and len(profile_data) > 0:
            profile = profile_data[0]
            stock_data['sector'] = profile.get('sector')
            stock_data['industry'] = profile.get('industry')
            stock_data['country'] = profile.get('country')
            stock_data['description'] = profile.get('description', '')[:200] + '...' if profile.get('description') else None
            stock_data['beta'] = profile.get('beta')  # Beta (volatility measure)
            stock_data['ceo'] = profile.get('ceo')
            stock_data['website'] = profile.get('website')
            stock_data['image'] = profile.get('image')
            
            # Calculate dividend yield if available
            last_div = profile.get('lastDiv', 0)
            if last_div and stock_data['currentPrice'] > 0:
                stock_data['dividendYield'] = round((last_div / stock_data['currentPrice']) * 100, 2)
                stock_data['lastDividend'] = last_div
            
        logger.info(f"Successfully fetched data for {ticker}")
        return stock_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return get_fallback_data(ticker)


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
        'priceChange': 0,
        'priceChangePercent': 0,
        'previousClose': 0,
        'marketCap': 'N/A',
        'sixMonthReturn': 0.0,
        'chartData': [],
        'pe': None,
        'ps': None,
        'pb': None,
        'beta': None,
        'evEbitda': None,
        'fiftyTwoWeekHigh': None,
        'fiftyTwoWeekLow': None,
        'volume': 0,
        'averageVolume': None,
        'dividendYield': None,
        'lastDividend': None,
        'sector': None,
        'industry': None,
        'country': None,
        'exchange': None,
        'description': None,
        'ceo': None,
        'website': None,
        'image': None,
        'targetMeanPrice': None,
        'recommendationKey': None,
        'numberOfAnalystOpinions': None,
        'news': None,
        'error': 'Data temporarily unavailable - check FMP_API_KEY'
    }


# Test function
if __name__ == "__main__":
    if not FMP_API_KEY:
        print("ERROR: FMP_API_KEY environment variable not set!")
        print("Please set: export FMP_API_KEY='your-api-key'")
        exit(1)
    
    print("Testing FMP Stable API...")
    print(f"API Key: {FMP_API_KEY[:10]}..." if FMP_API_KEY else "Not set")
    print()
    
    # Test with AAPL
    data = get_stock_data('AAPL')
    print(f"Ticker: {data['ticker']}")
    print(f"Name: {data['name']}")
    print(f"Price: ${data['currentPrice']}")
    print(f"Market Cap: {data['marketCap']}")
    print(f"Sector: {data['sector']}")
    print(f"Industry: {data['industry']}")
