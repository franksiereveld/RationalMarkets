"""
Production-ready financial data module using Financial Modeling Prep (FMP) API
Supports international markets, all securities types, and comprehensive financial data
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from functools import lru_cache
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FMP API Configuration
FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
FMP_BASE_URL = 'https://financialmodelingprep.com/stable'

if not FMP_API_KEY:
    logger.warning("FMP_API_KEY not set in environment variables")


def get_stock_data(ticker):
    """
    Get comprehensive stock data for a single ticker using FMP API
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock data including price, financials, and news
    """
    try:
        logger.info(f"Fetching data for {ticker} from FMP")
        
        # Get real-time quote
        quote = get_quote(ticker)
        if not quote:
            return get_fallback_data(ticker)
        
        # Get company profile
        profile = get_company_profile(ticker)
        
        # Get historical prices (6 months)
        historical = get_historical_prices(ticker, months=6)
        
        # Calculate 6-month return
        six_month_return = 0.0
        if historical and len(historical) >= 2:
            first_price = historical[0]['close']
            last_price = historical[-1]['close']
            six_month_return = ((last_price - first_price) / first_price) * 100
        
        # Format chart data
        chart_data = []
        for item in historical:
            chart_data.append({
                'date': item['date'],
                'price': round(item['close'], 2)
            })
        
        # Get financial ratios
        ratios = get_financial_ratios(ticker)
        
        # Get news
        news_data = get_stock_news(ticker, limit=5)
        
        # Build comprehensive response
        stock_data = {
            'ticker': ticker,
            'name': profile.get('companyName', ticker) if profile else ticker,
            'currentPrice': quote.get('price', 0),
            'marketCap': format_market_cap(profile.get('mktCap', 0) if profile else 0),
            'sixMonthReturn': round(six_month_return, 2),
            'chartData': chart_data,
            
            # Financial multiples from ratios
            'pe': ratios.get('peRatioTTM'),
            'ps': ratios.get('priceToSalesRatioTTM'),
            'pb': ratios.get('priceToBookRatioTTM'),
            'evEbitda': ratios.get('enterpriseValueMultipleTTM'),
            
            # Additional metrics
            'fiftyTwoWeekHigh': quote.get('yearHigh'),
            'fiftyTwoWeekLow': quote.get('yearLow'),
            'volume': quote.get('volume', 0),
            'averageVolume': quote.get('avgVolume'),
            'dividendYield': ratios.get('dividendYieldTTM'),
            
            # Company info
            'sector': profile.get('sector') if profile else None,
            'industry': profile.get('industry') if profile else None,
            'description': profile.get('description') if profile else None,
            'exchange': profile.get('exchangeShortName') if profile else None,
            'country': profile.get('country') if profile else None,
            
            # Analyst data (if available)
            'targetMeanPrice': None,  # Would need separate endpoint
            'recommendationKey': None,
            'numberOfAnalystOpinions': None,
            
            # News
            'news': news_data
        }
        
        logger.info(f"Successfully fetched data for {ticker}")
        return stock_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return get_fallback_data(ticker)


@lru_cache(maxsize=100)
def get_quote(ticker):
    """Get real-time quote for a ticker"""
    try:
        url = f"{FMP_BASE_URL}/quote?symbol={ticker}"
        params = {'apikey': FMP_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error fetching quote for {ticker}: {str(e)}")
        return None


@lru_cache(maxsize=100)
def get_company_profile(ticker):
    """Get company profile data"""
    try:
        url = f"{FMP_BASE_URL}/profile?symbol={ticker}"
        params = {'apikey': FMP_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error fetching profile for {ticker}: {str(e)}")
        return None


def get_historical_prices(ticker, months=6):
    """Get historical price data"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        url = f"{FMP_BASE_URL}/historical-chart/1day/{ticker}"
        params = {
            'apikey': FMP_API_KEY,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and 'historical' in data:
            # Return in chronological order (oldest first)
            return list(reversed(data['historical']))
        return []
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
        return []


@lru_cache(maxsize=100)
def get_financial_ratios(ticker):
    """Get financial ratios (TTM - Trailing Twelve Months)"""
    try:
        url = f"{FMP_BASE_URL}/ratios-ttm/{ticker}"
        params = {'apikey': FMP_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching ratios for {ticker}: {str(e)}")
        return {}


def get_stock_news(ticker, limit=5):
    """Get recent news for a stock"""
    try:
        url = f"{FMP_BASE_URL}/stock_news"
        params = {
            'apikey': FMP_API_KEY,
            'tickers': ticker,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
        
        news_items = []
        for item in data[:limit]:
            news_items.append({
                'headline': item.get('title', 'N/A'),
                'publisher': item.get('site', 'N/A'),
                'link': item.get('url', '#'),
                'date': item.get('publishedDate', 'N/A')[:10] if item.get('publishedDate') else 'N/A',
                'text': item.get('text', '')[:200] + '...' if item.get('text') else ''
            })
        
        return news_items if news_items else None
        
    except Exception as e:
        logger.warning(f"Could not fetch news for {ticker}: {str(e)}")
        return None


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
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    return results


def format_market_cap(market_cap):
    """Format market cap in billions or trillions"""
    if market_cap == 0 or market_cap is None:
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
        'marketCap': 'N/A',
        'sixMonthReturn': 0.0,
        'chartData': [],
        'pe': None,
        'ps': None,
        'pb': None,
        'evEbitda': None,
        'fiftyTwoWeekHigh': None,
        'fiftyTwoWeekLow': None,
        'volume': 0,
        'averageVolume': None,
        'dividendYield': None,
        'sector': None,
        'industry': None,
        'description': None,
        'exchange': None,
        'country': None,
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
        print("Please sign up at https://site.financialmodelingprep.com/")
        print("Then set: export FMP_API_KEY='your-api-key'")
        exit(1)
    
    print("Testing FMP financial data module...")
    print(f"API Key: {FMP_API_KEY[:10]}..." if FMP_API_KEY else "Not set")
    print()
    
    # Test single stock
    print("="*60)
    print("Testing AAPL (Apple):")
    print("="*60)
    aapl_data = get_stock_data("AAPL")
    
    print(f"\nBasic Info:")
    print(f"  Ticker: {aapl_data['ticker']}")
    print(f"  Name: {aapl_data['name']}")
    print(f"  Current Price: ${aapl_data['currentPrice']}")
    print(f"  Market Cap: {aapl_data['marketCap']}")
    print(f"  6M Return: {aapl_data['sixMonthReturn']}%")
    print(f"  Exchange: {aapl_data['exchange']}")
    print(f"  Country: {aapl_data['country']}")
    
    print(f"\nFinancial Multiples:")
    print(f"  P/E Ratio: {aapl_data['pe']}")
    print(f"  P/S Ratio: {aapl_data['ps']}")
    print(f"  P/B Ratio: {aapl_data['pb']}")
    print(f"  EV/EBITDA: {aapl_data['evEbitda']}")
    
    print(f"\nChart Data Points: {len(aapl_data['chartData'])}")
    if aapl_data['chartData']:
        print(f"  First: {aapl_data['chartData'][0]}")
        print(f"  Last: {aapl_data['chartData'][-1]}")
    
    if aapl_data.get('news'):
        print(f"\nRecent News ({len(aapl_data['news'])} items):")
        for item in aapl_data['news'][:3]:
            print(f"  - {item['headline']}")
            print(f"    ({item['publisher']}, {item['date']})")
    
    print(f"\n{'='*60}")
    print("✅ FMP API Test Complete!")
    print("="*60)

