"""
Enhanced Financial data module using Manus API Hub
Provides comprehensive stock data including insights, outlooks, and news
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
    Get comprehensive stock data for a single ticker including insights
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock data including price, financials, insights, and news
    """
    if not MANUS_API_AVAILABLE:
        return get_fallback_data(ticker)
    
    try:
        client = ApiClient()
        
        # Get stock chart data (price and historical data)
        chart_response = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': ticker,
            'region': 'US',
            'interval': '1d',
            'range': '6mo',
            'includeAdjustedClose': True
        })
        
        # Get stock insights (outlooks, news, analyst reports)
        insights_response = client.call_api('YahooFinance/get_stock_insights', query={
            'symbol': ticker
        })
        
        if not chart_response or 'chart' not in chart_response or 'result' not in chart_response['chart']:
            return get_fallback_data(ticker)
        
        result = chart_response['chart']['result'][0]
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
        
        # Extract insights data
        insights_data = extract_insights(insights_response, ticker)
        
        # Build response (flattened structure for frontend compatibility)
        stock_data = {
            'ticker': ticker,
            'name': meta.get('longName', meta.get('shortName', ticker)),
            'currentPrice': meta.get('regularMarketPrice', 0),
            'marketCap': format_market_cap(meta.get('marketCap', meta.get('regularMarketCap', 0))),
            'sixMonthReturn': round(six_month_return, 2),
            'chartData': chart_data,
            'pe': insights_data.get('pe'),
            'ps': insights_data.get('ps'),
            'pb': insights_data.get('pb'),
            'evEbitda': insights_data.get('evEbitda'),
            'fiftyTwoWeekHigh': meta.get('fiftyTwoWeekHigh', None),
            'fiftyTwoWeekLow': meta.get('fiftyTwoWeekLow', None),
            'volume': meta.get('regularMarketVolume', 0),
            # Enhanced data from insights
            'valuation': insights_data.get('valuation'),
            'outlook': insights_data.get('outlook'),
            'companyMetrics': insights_data.get('companyMetrics'),
            'analystReport': insights_data.get('analystReport'),
            'news': insights_data.get('news')
        }
        
        return stock_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return get_fallback_data(ticker)


def extract_insights(insights_response, ticker):
    """
    Extract relevant insights from the Yahoo Finance insights API response
    
    Args:
        insights_response (dict): Raw insights API response
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Extracted insights data
    """
    insights_data = {
        'pe': None,
        'ps': None,
        'pb': None,
        'evEbitda': None,
        'valuation': None,
        'outlook': None,
        'companyMetrics': None,
        'analystReport': None,
        'news': None
    }
    
    if not insights_response or 'finance' not in insights_response:
        return insights_data
    
    try:
        result = insights_response['finance'].get('result', {})
        
        # Extract valuation
        instrument_info = result.get('instrumentInfo', {})
        if 'valuation' in instrument_info:
            val = instrument_info['valuation']
            insights_data['valuation'] = {
                'description': val.get('description', 'N/A'),
                'discount': val.get('discount', 'N/A')
            }
        
        # Extract technical outlooks
        if 'technicalEvents' in instrument_info:
            tech = instrument_info['technicalEvents']
            outlooks = {}
            
            for term in ['shortTermOutlook', 'intermediateTermOutlook', 'longTermOutlook']:
                if term in tech:
                    outlook = tech[term]
                    outlooks[term.replace('Outlook', '')] = {
                        'direction': outlook.get('direction', 'N/A'),
                        'score': outlook.get('score', 0),
                        'description': outlook.get('scoreDescription', 'N/A')
                    }
            
            if outlooks:
                insights_data['outlook'] = outlooks
        
        # Extract company metrics
        company_snapshot = result.get('companySnapshot', {})
        if 'company' in company_snapshot:
            company = company_snapshot['company']
            insights_data['companyMetrics'] = {
                'innovativeness': round(company.get('innovativeness', 0) * 100, 1),
                'hiring': round(company.get('hiring', 0) * 100, 1),
                'sustainability': round(company.get('sustainability', 0) * 100, 1),
                'insiderSentiments': round(company.get('insiderSentiments', 0) * 100, 1),
                'earningsReports': round(company.get('earningsReports', 0) * 100, 1)
            }
        
        # Extract analyst report (most recent)
        reports = result.get('reports', [])
        if reports and len(reports) > 0:
            report = reports[0]  # Most recent report
            insights_data['analystReport'] = {
                'provider': report.get('provider', 'N/A'),
                'rating': report.get('investmentRating', 'N/A'),
                'targetPrice': report.get('targetPrice'),
                'date': report.get('reportDate', 'N/A')
            }
        
        # Extract news/significant developments
        sig_devs = result.get('sigDevs', [])
        if sig_devs and len(sig_devs) > 0:
            insights_data['news'] = []
            for dev in sig_devs[:3]:  # Top 3 news items
                insights_data['news'].append({
                    'headline': dev.get('headline', 'N/A'),
                    'date': dev.get('date', 'N/A')
                })
        
    except Exception as e:
        print(f"Error extracting insights for {ticker}: {str(e)}")
    
    return insights_data


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
        'valuation': None,
        'outlook': None,
        'companyMetrics': None,
        'analystReport': None,
        'news': None,
        'error': 'Data temporarily unavailable'
    }


# Test function
if __name__ == "__main__":
    print("Testing enhanced financial data module...")
    
    # Test single stock
    print("\nTesting DELL:")
    dell_data = get_stock_data("DELL")
    print(f"Ticker: {dell_data['ticker']}")
    print(f"Name: {dell_data['name']}")
    print(f"Current Price: ${dell_data['currentPrice']}")
    print(f"Market Cap: {dell_data['marketCap']}")
    print(f"6M Return: {dell_data['sixMonthReturn']}%")
    
    if dell_data.get('valuation'):
        print(f"\nValuation: {dell_data['valuation']['description']} ({dell_data['valuation']['discount']} discount)")
    
    if dell_data.get('outlook'):
        print(f"\nOutlooks:")
        for term, outlook in dell_data['outlook'].items():
            print(f"  {term}: {outlook['direction']} - {outlook['description']}")
    
    if dell_data.get('analystReport'):
        report = dell_data['analystReport']
        print(f"\nAnalyst Report:")
        print(f"  Rating: {report['rating']}")
        print(f"  Target Price: ${report['targetPrice']}")
        print(f"  Provider: {report['provider']}")
    
    if dell_data.get('news'):
        print(f"\nRecent News:")
        for item in dell_data['news']:
            print(f"  - {item['headline']} ({item['date']})")
    
    print(f"\nChart data points: {len(dell_data['chartData'])}")

