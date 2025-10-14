"""
Production-ready financial data module using yfinance
Works in any environment (sandbox, Railway, local, etc.)
Provides comprehensive stock data including price, financials, and news
Includes rate limiting protection and retry logic
"""

import yfinance as yf
from datetime import datetime, timedelta
import logging
import time
from functools import lru_cache
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure yfinance to use a proper user agent
import requests_cache
session = requests_cache.CachedSession('yfinance.cache', expire_after=300)  # 5 minute cache
session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def get_stock_data(ticker, retry_count=0, max_retries=3):
    """
    Get comprehensive stock data for a single ticker with retry logic
    
    Args:
        ticker (str): Stock ticker symbol
        retry_count (int): Current retry attempt
        max_retries (int): Maximum number of retries
        
    Returns:
        dict: Stock data including price, financials, insights, and news
    """
    try:
        logger.info(f"Fetching data for {ticker} (attempt {retry_count + 1}/{max_retries + 1})")
        
        # Add random delay to avoid rate limiting (between 0.5-2 seconds)
        if retry_count > 0:
            delay = min(2 ** retry_count, 10) + random.uniform(0, 1)  # Exponential backoff
            logger.info(f"Waiting {delay:.1f}s before retry...")
            time.sleep(delay)
        else:
            time.sleep(random.uniform(0.3, 0.8))  # Small random delay
        
        # Create ticker object with session
        stock = yf.Ticker(ticker, session=session)
        
        # Get stock info
        try:
            info = stock.info
        except Exception as e:
            logger.warning(f"Could not fetch info for {ticker}: {str(e)}")
            if retry_count < max_retries and "429" in str(e):
                return get_stock_data(ticker, retry_count + 1, max_retries)
            info = {}
        
        # Get historical data (6 months)
        try:
            hist = stock.history(period="6mo")
        except Exception as e:
            logger.warning(f"Could not fetch history for {ticker}: {str(e)}")
            if retry_count < max_retries and "429" in str(e):
                return get_stock_data(ticker, retry_count + 1, max_retries)
            hist = None
        
        if hist is None or hist.empty:
            logger.warning(f"No historical data for {ticker}")
            return get_fallback_data(ticker)
        
        # Calculate 6-month return
        close_prices = hist['Close'].dropna()
        six_month_return = 0.0
        if len(close_prices) >= 2:
            six_month_return = ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100
        
        # Format chart data
        chart_data = []
        for date, row in hist.iterrows():
            if not pd.isna(row['Close']):
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': round(float(row['Close']), 2)
                })
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        if current_price == 0 and len(close_prices) > 0:
            current_price = float(close_prices.iloc[-1])
        
        # Get market cap
        market_cap = info.get('marketCap', 0)
        
        # Get financial multiples
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        ps_ratio = info.get('priceToSalesTrailing12Months')
        pb_ratio = info.get('priceToBook')
        ev_ebitda = info.get('enterpriseToEbitda')
        
        # Get news (with error handling)
        news_data = get_stock_news(stock)
        
        # Build comprehensive response
        stock_data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName', ticker),
            'currentPrice': round(current_price, 2),
            'marketCap': format_market_cap(market_cap),
            'sixMonthReturn': round(six_month_return, 2),
            'chartData': chart_data,
            
            # Financial multiples
            'pe': round(pe_ratio, 2) if pe_ratio else None,
            'ps': round(ps_ratio, 2) if ps_ratio else None,
            'pb': round(pb_ratio, 2) if pb_ratio else None,
            'evEbitda': round(ev_ebitda, 2) if ev_ebitda else None,
            
            # Additional metrics
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
            'volume': info.get('volume', 0),
            'averageVolume': info.get('averageVolume'),
            'dividendYield': info.get('dividendYield'),
            
            # Company info
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'description': info.get('longBusinessSummary'),
            
            # Analyst data
            'targetMeanPrice': info.get('targetMeanPrice'),
            'recommendationKey': info.get('recommendationKey'),
            'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions'),
            
            # News
            'news': news_data
        }
        
        logger.info(f"Successfully fetched data for {ticker}")
        return stock_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        
        # Retry on rate limit errors
        if retry_count < max_retries and ("429" in str(e) or "Too Many Requests" in str(e)):
            logger.info(f"Rate limited, retrying {ticker}...")
            return get_stock_data(ticker, retry_count + 1, max_retries)
        
        return get_fallback_data(ticker)


def get_stock_news(stock):
    """
    Get recent news for a stock
    
    Args:
        stock: yfinance Ticker object
        
    Returns:
        list: List of news items with headline, publisher, and link
    """
    try:
        news = stock.news
        if not news:
            return None
        
        news_items = []
        for item in news[:5]:  # Top 5 news items
            news_items.append({
                'headline': item.get('title', 'N/A'),
                'publisher': item.get('publisher', 'N/A'),
                'link': item.get('link', '#'),
                'date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d') if item.get('providerPublishTime') else 'N/A'
            })
        
        return news_items if news_items else None
        
    except Exception as e:
        logger.warning(f"Could not fetch news: {str(e)}")
        return None


def get_multiple_stocks_data(tickers):
    """
    Get stock data for multiple tickers with proper delays
    
    Args:
        tickers (list): List of stock ticker symbols
        
    Returns:
        dict: Dictionary mapping tickers to their stock data
    """
    results = {}
    for i, ticker in enumerate(tickers):
        # Add delay between requests (except for first one)
        if i > 0:
            delay = random.uniform(1.0, 2.0)
            logger.info(f"Waiting {delay:.1f}s before next request...")
            time.sleep(delay)
        
        results[ticker] = get_stock_data(ticker)
    
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
        'targetMeanPrice': None,
        'recommendationKey': None,
        'numberOfAnalystOpinions': None,
        'news': None,
        'error': 'Data temporarily unavailable'
    }


# Import pandas (needed for data processing)
try:
    import pandas as pd
except ImportError:
    logger.error("pandas not installed - required for yfinance")
    pd = None


# Test function
if __name__ == "__main__":
    print("Testing production financial data module with yfinance...")
    print("Note: Using caching and rate limiting to avoid 429 errors\n")
    
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
    
    print(f"\nFinancial Multiples:")
    print(f"  P/E Ratio: {aapl_data['pe']}")
    print(f"  P/S Ratio: {aapl_data['ps']}")
    print(f"  P/B Ratio: {aapl_data['pb']}")
    print(f"  EV/EBITDA: {aapl_data['evEbitda']}")
    
    print(f"\nChart Data Points: {len(aapl_data['chartData'])}")
    if aapl_data['chartData']:
        print(f"  First: {aapl_data['chartData'][0]}")
        print(f"  Last: {aapl_data['chartData'][-1]}")

