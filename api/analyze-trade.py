"""
RationalMarkets AI Trade Analysis API
Serverless function for analyzing trade ideas using OpenAI
"""

import json
import os
from openai import OpenAI

def handler(event, context):
    """
    Serverless function handler for trade analysis
    Compatible with Vercel, Netlify, and AWS Lambda
    """
    
    # Parse request body
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        trade_name = body.get('tradeName', '')
        trade_description = body.get('tradeDescription', '')
        
        if not trade_name or not trade_description:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Both tradeName and tradeDescription are required'
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Invalid request format: {str(e)}'
            })
        }
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'OpenAI API configuration error'
            })
        }
    
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
Consider both the upside potential and downside risks."""

    user_prompt = f"""Trade Idea: {trade_name}

Description: {trade_description}

Please analyze this investment idea and provide specific stock recommendations with a complete long/short strategy."""

    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # Using the available model
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
        
        # Add metadata
        result = {
            "tradeName": trade_name,
            "date": "Current Date",
            "owner": "Current User",
            **ai_analysis
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'AI analysis failed: {str(e)}'
            })
        }


# Flask wrapper for local testing
if __name__ == '__main__':
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/api/analyze-trade', methods=['POST', 'OPTIONS'])
    def analyze_trade():
        if request.method == 'OPTIONS':
            return '', 204
        
        event = {
            'body': request.get_json()
        }
        response = handler(event, None)
        return jsonify(json.loads(response['body'])), response['statusCode']
    
    print("Starting RationalMarkets AI Analysis API on http://localhost:5000")
    app.run(debug=True, port=5000)

