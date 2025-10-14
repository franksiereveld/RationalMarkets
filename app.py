#!/usr/bin/env python3
"""
RationalMarkets AI Analysis API Server
AI-powered trade analysis with real Yahoo Finance market data
Serves both API endpoints and frontend static files
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Add current directory to path
sys.path.append('/home/ubuntu/RationalMarkets')
from trade_analyzer import analyze_trade_with_ai

# Initialize Flask app - serve static files from current directory
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# API ENDPOINTS
# ============================================================================

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

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main landing page"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """Serve any file from the root directory"""
    try:
        return send_from_directory(BASE_DIR, filename)
    except:
        return "File not found", 404

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"{'='*80}")
    print(f"RationalMarkets - AI-Powered Trade Analysis")
    print(f"{'='*80}")
    print(f"Server: http://localhost:{port}")
    print(f"\nFrontend:")
    print(f"  GET  / - Landing page")
    print(f"  GET  /my-trades.html - Trade analysis interface")
    print(f"  GET  /ai-analysis.html - AI analysis results")
    print(f"  GET  /ai-strategy.html - Strategy demo")
    print(f"\nAPI Endpoints:")
    print(f"  POST /api/analyze-trade - AI trade analysis with real market data")
    print(f"  GET  /health - Health check")
    print(f"{'='*80}")
    print(f"Press Ctrl+C to stop")
    print(f"{'='*80}\n")
    app.run(host='0.0.0.0', port=port, debug=False)

