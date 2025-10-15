#!/usr/bin/env python3.11
"""
AI-Powered Trade Analysis System
Analyzes user trade ideas and recommends specific positions with real market data
"""
import os
import sys
import json
from openai import OpenAI
from datetime import datetime
sys.path.append('/home/ubuntu/RationalMarkets')

# Use yfinance as primary (free, no API key needed, delayed data 15-20 min)
try:
    from financial_data_production import get_stock_data
    print("Using yfinance for market data (free, delayed 15-20 min)")
except ImportError:
    # Fallback to sandbox version
    from financial_data import get_stock_data
    print("Using sandbox financial data module (Manus API Hub)")

# Initialize OpenAI client (API key already in environment)
client = OpenAI()
# Initialize OpenAI client (API key already in environment)
client = OpenAI()
def analyze_trade_with_ai(trade_name: str, trade_description: str) -> dict:
    """
    Analyze a trade idea using AI and return recommendations with real market data
    
    Args:
        trade_name: Name of the trade strategy
        trade_description: Detailed description of the trade thesis
        
    Returns:
        Complete trade analysis with positions, allocations, and market data
    """
    
    # Step 1: Get AI recommendations
    print(f"Analyzing trade: {trade_name}")
    ai_recommendations = get_ai_recommendations(trade_name, trade_description)
    
    # Step 2: Fetch real market data for each ticker
    print("Fetching market data for recommended tickers...")
    enriched_analysis = enrich_with_market_data(ai_recommendations)
    
    return enriched_analysis


def get_ai_recommendations(trade_name: str, trade_description: str) -> dict:
    """
    Call OpenAI to analyze the trade and recommend specific positions
    """
    
    prompt = f"""You are an expert financial analyst and portfolio manager. A user has proposed the following trade idea:

**Trade Name:** {trade_name}

**Trade Description:** {trade_description}

Please analyze this trade idea and recommend specific stocks, indices, and derivatives to implement it.

**Your response must be in valid JSON format with this exact structure:**

{{
  "tradeName": "{trade_name}",
  "recommendation": "RECOMMENDED" or "NOT RECOMMENDED" or "CONDITIONAL",
  "riskLevel": "LOW" or "MODERATE" or "HIGH" or "VERY HIGH",
  "longs": [
    {{
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "allocation": "25%",
      "securityType": "equity",
      "rationale": "Why this position supports the trade thesis"
    }}
  ],
  "shorts": [
    {{
      "ticker": "TSLA",
      "name": "Tesla Inc.",
      "allocation": "15%",
      "securityType": "equity",
      "rationale": "Why shorting this supports the trade thesis"
    }}
  ],
  "derivatives": [
    {{
      "ticker": "SPY",
      "name": "SPDR S&P 500 ETF Put Options",
      "allocation": "10%",
      "securityType": "option",
      "positionType": "long",
      "rationale": "Why this derivative position supports the trade"
    }}
  ],
  "returnEstimates": {{
    "1M": "5.2%",
    "3M": "12.5%",
    "6M": "22.3%",
    "1Y": "35.8%",
    "3Y": "95.4%"
  }},
  "aiRationale": "Overall explanation of the trade strategy, why these positions work together, key risks, and return expectations"
}}

**Important Guidelines:**
1. **Security Types:** equity, fixed_income, index, future, option
2. **Position Types:** For derivatives, specify "long" or "short"
3. **Allocations:** Must sum to approximately 100% across all positions
4. **Tickers:** Use valid stock/ETF/index tickers (e.g., AAPL, SPY, QQQ, VIX, ^GSPC)
5. **Use Your Judgment:** You can add shorts, hedges, or derivatives if they improve the strategy, even if not explicitly mentioned by the user
6. **Empty Arrays:** If no positions in a category, use empty array: []
7. **Return Estimates:** Be realistic based on the strategy and market conditions
8. **Rationale:** Each position should have clear reasoning tied to the trade thesis

Provide your complete analysis in valid JSON format only, no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        
        ai_response = ai_response.strip()
        
        # Parse JSON
        recommendations = json.loads(ai_response)
        
        # Add metadata
        recommendations['date'] = datetime.now().strftime('%Y-%m-%d')
        recommendations['owner'] = 'Current User'
        
        return recommendations
        
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        raise


def enrich_with_market_data(recommendations: dict) -> dict:
    """
    Fetch real market data from Yahoo Finance for each recommended ticker
    """
    
    # Process longs
    if 'longs' in recommendations and recommendations['longs']:
        for position in recommendations['longs']:
            ticker = position['ticker']
            print(f"  Fetching data for {ticker} (long)...")
            market_data = get_stock_data(ticker)
            position.update(market_data)
            position['positionType'] = 'long'
    
    # Process shorts
    if 'shorts' in recommendations and recommendations['shorts']:
        for position in recommendations['shorts']:
            ticker = position['ticker']
            print(f"  Fetching data for {ticker} (short)...")
            market_data = get_stock_data(ticker)
            position.update(market_data)
            position['positionType'] = 'short'
    
    # Process derivatives
    if 'derivatives' in recommendations and recommendations['derivatives']:
        for position in recommendations['derivatives']:
            ticker = position['ticker']
            print(f"  Fetching data for {ticker} (derivative)...")
            # For derivatives, try to get underlying data
            underlying_ticker = ticker.replace(' Put', '').replace(' Call', '').split()[0]
            market_data = get_stock_data(underlying_ticker)
            position.update(market_data)
            # positionType already set by AI
    
    return recommendations


def calculate_missing_multiples(stock_data: dict) -> dict:
    """
    Calculate financial multiples if not available from API
    """
    
    # P/E = Price / EPS
    if stock_data.get('price') and stock_data.get('eps'):
        if not stock_data.get('pe_ratio'):
            stock_data['pe_ratio'] = round(stock_data['price'] / stock_data['eps'], 2)
    
    # P/S = Market Cap / Revenue
    if stock_data.get('marketCap') and stock_data.get('revenue'):
        if not stock_data.get('ps_ratio'):
            stock_data['ps_ratio'] = round(stock_data['marketCap'] / stock_data['revenue'], 2)
    
    # P/B = Price / Book Value Per Share
    if stock_data.get('price') and stock_data.get('bookValue'):
        if not stock_data.get('pb_ratio'):
            stock_data['pb_ratio'] = round(stock_data['price'] / stock_data['bookValue'], 2)
    
    return stock_data


# Test function
if __name__ == "__main__":
    # Test with AI Bubble Short Strategy
    test_trade = {
        "name": "AI Bubble Short Strategy",
        "description": "I believe AI stocks are in a bubble and want to short the most overvalued ones like NVIDIA and Tesla while hedging with volatility."
    }
    
    print("=" * 80)
    print("Testing AI Trade Analyzer")
    print("=" * 80)
    
    result = analyze_trade_with_ai(test_trade['name'], test_trade['description'])
    
    print("\n" + "=" * 80)
    print("ANALYSIS RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2))

