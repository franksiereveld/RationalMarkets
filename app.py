#!/usr/bin/env python3.11
"""
RationalMarkets AI Analysis API Server
AI-powered trade analysis with real Yahoo Finance market data
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to path
sys.path.append('/home/ubuntu/RationalMarkets')
from trade_analyzer import analyze_trade_with_ai

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/analyze-trade', methods=['POST', 'OPTIONS'])
def analyze_trade():
    """Analyze a trade idea using AI with real market data"""
    
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
        
        print(f"\n{'='*80}")
        print(f"Analyzing Trade: {trade_name}")
        print(f"{'='*80}\n")
        
        # Call AI trade analyzer with Yahoo Finance integration
        result = analyze_trade_with_ai(trade_name, trade_description)
        
        print(f"\n{'='*80}")
        print(f"Analysis Complete")
        print(f"{'='*80}\n")
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'RationalMarkets API'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"{'='*80}")
    print(f"RationalMarkets AI Analysis API")
    print(f"{'='*80}")
    print(f"Server: http://localhost:{port}")
    print(f"Endpoints:")
    print(f"  POST /api/analyze-trade - AI trade analysis with real market data")
    print(f"  GET  /health - Health check")
    print(f"{'='*80}")
    print(f"Press Ctrl+C to stop")
    print(f"{'='*80}\n")
    app.run(host='0.0.0.0', port=port, debug=False)

