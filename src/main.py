"""
Global AI Long/Short Strategy MVP - Web Application

Flask web application that provides a unified dashboard for testing the Global AI Long/Short
investment strategy accessible through both Alpaca and Swissquote APIs worldwide.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Import both broker APIs and strategies
from strategy import AILongShortStrategy, PortfolioAllocation
from global_strategy import GlobalAILongShortStrategy
from swissquote_api import SwissquoteAPI

# Try to import Alpaca API
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("Alpaca Trade API not available. Install with: pip install alpaca-trade-api")

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global instances
global_strategy = GlobalAILongShortStrategy()
broker_clients = {}
current_broker = 'alpaca'  # Default broker

def get_broker_client(broker_type, credentials=None):
    """Get or create broker client instance"""
    global broker_clients
    
    if broker_type == 'alpaca':
        if broker_type not in broker_clients or credentials:
            if credentials:
                api_key = credentials.get('apiKey')
                secret_key = credentials.get('secretKey')
                paper_mode = credentials.get('paperMode', True)
            else:
                api_key = os.getenv('ALPACA_API_KEY')
                secret_key = os.getenv('ALPACA_SECRET_KEY')
                paper_mode = True
            
            base_url = 'https://paper-api.alpaca.markets' if paper_mode else 'https://api.alpaca.markets'
            
            if ALPACA_AVAILABLE and api_key and secret_key:
                try:
                    broker_clients[broker_type] = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
                except Exception as e:
                    print(f"Failed to initialize Alpaca client: {e}")
                    broker_clients[broker_type] = None
            else:
                broker_clients[broker_type] = None
                
    elif broker_type == 'swissquote':
        if broker_type not in broker_clients or credentials:
            if credentials:
                client_id = credentials.get('clientId')
                client_secret = credentials.get('clientSecret')
                demo_mode = credentials.get('demoMode', True)
            else:
                client_id = os.getenv('SWISSQUOTE_CLIENT_ID')
                client_secret = os.getenv('SWISSQUOTE_CLIENT_SECRET')
                demo_mode = True
            
            try:
                broker_clients[broker_type] = SwissquoteAPI(
                    client_id=client_id,
                    client_secret=client_secret,
                    demo_mode=demo_mode
                )
            except Exception as e:
                print(f"Failed to initialize Swissquote client: {e}")
                broker_clients[broker_type] = None
    
    return broker_clients.get(broker_type)

def get_broker_info(broker_type):
    """Get broker information"""
    if broker_type == 'alpaca':
        return {
            'name': 'Alpaca Markets',
            'region': 'United States',
            'currency': 'USD',
            'type': 'alpaca',
            'markets': 'US Stocks, ETFs',
            'demo_available': True
        }
    elif broker_type == 'swissquote':
        return {
            'name': 'Swissquote',
            'region': 'Global',
            'currency': 'Multi-Currency (CHF, EUR, USD, GBP)',
            'type': 'swissquote',
            'markets': 'Global Stocks, ETFs, Bonds, Crypto',
            'demo_available': True
        }
    else:
        return {'name': 'Unknown', 'type': 'unknown'}

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/strategy/summary')
def get_strategy_summary():
    """Get strategy summary for selected broker"""
    broker = request.args.get('broker', 'alpaca')
    
    try:
        summary = global_strategy.get_strategy_summary()
        broker_info = get_broker_info(broker)
        
        # Add broker-specific information
        summary.update({
            'broker': broker_info,
            'base_currency': 'USD' if broker == 'alpaca' else 'CHF'
        })
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_broker_connection():
    """Test broker API connection"""
    data = request.get_json()
    broker = data.get('broker')
    credentials = data.get('credentials')
    
    try:
        client = get_broker_client(broker, credentials)
        
        if client is None:
            return jsonify({'success': False, 'error': 'Failed to create broker client'})
        
        # Test connection based on broker type
        if broker == 'alpaca':
            if ALPACA_AVAILABLE:
                account = client.get_account()
                return jsonify({'success': True, 'account_id': account.id})
            else:
                return jsonify({'success': False, 'error': 'Alpaca API not available'})
        elif broker == 'swissquote':
            account_info = client.get_account_info()
            return jsonify({'success': True, 'account_id': account_info.get('account_id')})
        else:
            return jsonify({'success': False, 'error': 'Unknown broker type'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/calculate-orders', methods=['POST'])
def calculate_orders():
    """Calculate trade orders for selected broker"""
    data = request.get_json()
    broker = data.get('broker', 'alpaca')
    portfolio_value = data.get('portfolio_value')
    allocation_percentage = data.get('allocation_percentage')
    credentials = data.get('credentials')
    
    try:
        # Get broker client
        client = get_broker_client(broker, credentials)
        
        # Calculate orders using global strategy
        orders = global_strategy.calculate_trade_orders(
            portfolio_value=portfolio_value,
            allocation_percentage=allocation_percentage,
            broker_type=broker
        )
        
        return jsonify({
            'success': True,
            'orders': orders,
            'broker': broker,
            'total_orders': len(orders)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute-orders', methods=['POST'])
def execute_orders():
    """Execute trade orders via selected broker"""
    data = request.get_json()
    broker = data.get('broker', 'alpaca')
    orders = data.get('orders', [])
    credentials = data.get('credentials')
    
    try:
        # Get broker client
        client = get_broker_client(broker, credentials)
        
        if client is None:
            return jsonify({'success': False, 'error': 'Broker client not available'})
        
        # Execute orders using global strategy
        results = global_strategy.execute_orders(orders, broker_type=broker, client=client)
        
        return jsonify({
            'success': True,
            'results': results,
            'broker': broker,
            'executed_orders': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/account/status')
def get_account_status():
    """Get account status for selected broker"""
    broker = request.args.get('broker', 'alpaca')
    
    try:
        client = get_broker_client(broker)
        
        if client is None:
            return jsonify({
                'demo_mode': True,
                'broker': get_broker_info(broker),
                'status': 'Demo Mode - No API Connection'
            })
        
        if broker == 'alpaca' and ALPACA_AVAILABLE:
            account = client.get_account()
            return jsonify({
                'demo_mode': False,
                'broker': get_broker_info(broker),
                'account_id': account.id,
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'status': account.status
            })
        elif broker == 'swissquote':
            account_info = client.get_account_info()
            return jsonify({
                'demo_mode': client.demo_mode,
                'broker': get_broker_info(broker),
                'account_id': account_info.get('account_id'),
                'buying_power': account_info.get('buying_power'),
                'portfolio_value': account_info.get('portfolio_value'),
                'status': account_info.get('status')
            })
        else:
            return jsonify({'error': 'Unknown broker or API not available'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the application
    print("🚀 Starting Global AI Long/Short Strategy MVP")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🌍 Supports both Alpaca (US) and Swissquote (Global) brokers")
    print("⚙️  Use the dashboard to select and configure your preferred broker")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

