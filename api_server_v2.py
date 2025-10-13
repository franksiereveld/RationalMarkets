#!/usr/bin/env python3
"""
RationalMarkets AI Analysis API Server v2
Includes OpenAI trade analysis + Real financial data
"""

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from financial_data import get_stock_data, get_multiple_stocks_data

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/api/analyze-trade', methods=['POST', 'OPTIONS'])
def analyze_trade():
    """Analyze a trade idea using OpenAI and enrich with real financial data"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Parse request
        data = request.get_json()
        trade_name = data.get('tradeName', '').strip()
        trade_description = data.get('tradeDescription', '').strip()
        
        if not trade_name or not trade_description:
            return jsonify({
                'error': 'Both tradeName and tradeDescription are required'
            }), 400
        
        # Create AI analysis prompt
        system_prompt = """You are a professional investment analyst specializing in long/short equity strategies. 
Your role is to analyze investment ideas and provide specific, actionable stock recommendations.

For each trade idea, provide:
1. 3-5 specific stock recommendations (with ticker symbols)
2. Position type (long or short) for each stock
3. Allocation percentage for each position
4. Brief rationale for each recommendation
5. Overall strategy rationale
6. Risk assessment (LOW, MODERATE, HIGH)
7. Expected return estimates (1M, 3M, 6M, 1Y, 3Y)

Return your analysis in the following JSON format:
{
    "recommendation": "RECOMMENDED" or "NOT RECOMMENDED",
    "riskLevel": "LOW" or "MODERATE" or "HIGH",
    "longPositions": [
        {
            "symbol": "TICKER",
            "name": "Company Name",
            "allocation": "XX%",
            "rationale": "Brief explanation"
        }
    ],
    "shortPositions": [
        {
            "symbol": "TICKER",
            "name": "Company Name",
            "allocation": "XX%",
            "rationale": "Brief explanation"
        }
    ],
    "returnEstimates": {
        "1M": "X.X%",
        "3M": "X.X%",
        "6M": "X.X%",
        "1Y": "X.X%",
        "3Y": "X.X%"
    },
    "aiRationale": "Comprehensive analysis of the strategy, including thesis, risks, and potential outcomes."
}

Be specific with ticker symbols. Ensure allocations add up to 100%. Be realistic with return estimates.
Consider both the upside potential and downside risks. For short strategies, return estimates can be negative."""

        user_prompt = f"""Trade Idea: {trade_name}

Description: {trade_description}

Please analyze this investment idea and provide specific stock recommendations with a complete long/short strategy."""

        # Call OpenAI API
        print(f"Calling OpenAI for trade: {trade_name}")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse AI response
        ai_analysis = json.loads(response.choices[0].message.content)
        
        # Extract all stock symbols
        all_symbols = []
        for pos in ai_analysis.get('longPositions', []):
            all_symbols.append(pos['symbol'])
        for pos in ai_analysis.get('shortPositions', []):
            all_symbols.append(pos['symbol'])
        
        # Fetch real financial data for all symbols
        print(f"Fetching financial data for: {all_symbols}")
        financial_data = get_multiple_stocks_data(all_symbols)
        
        # Enrich positions with real financial data
        for pos in ai_analysis.get('longPositions', []):
            symbol = pos['symbol'].upper()
            if symbol in financial_data:
                pos['financialData'] = financial_data[symbol]
        
        for pos in ai_analysis.get('shortPositions', []):
            symbol = pos['symbol'].upper()
            if symbol in financial_data:
                pos['financialData'] = financial_data[symbol]
        
        # Add metadata
        result = {
            "tradeName": trade_name,
            "date": datetime.now().strftime("%m/%d/%Y"),
            "owner": "Current User",
            **ai_analysis
        }
        
        print(f"Analysis complete for: {trade_name}")
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/api/stock-data/<symbol>', methods=['GET'])
def get_stock_info(symbol):
    """Get financial data for a single stock"""
    try:
        data = get_stock_data(symbol)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch stock data: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': 'v2'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print(f"Starting RationalMarkets AI Analysis API v2 on http://localhost:{port}")
    print("Features: OpenAI Analysis + Real Financial Data")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=port, debug=False)