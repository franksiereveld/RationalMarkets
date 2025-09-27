# Broker Integration Technical Documentation

## Overview

This document provides technical details for integrating both Alpaca Markets and Swissquote brokers with the AI Long/Short Strategy platform. The platform supports dynamic broker switching and maintains a unified API interface.

## Architecture

### Broker Abstraction Layer

The platform uses a unified broker abstraction that allows seamless switching between different broker APIs:

```python
# Unified broker client management
broker_clients = {
    'alpaca': AlpacaClient,
    'swissquote': SwissquoteClient
}

# Dynamic broker selection
current_broker = user_selected_broker
client = get_broker_client(current_broker, credentials)
```

### Global Strategy Implementation

The `GlobalAILongShortStrategy` class provides broker-agnostic strategy logic:

- **Unified Position Management**: Same strategy positions across all brokers
- **Symbol Mapping**: Automatic symbol translation (e.g., ASML.AS vs ASML ADR)
- **Currency Handling**: Multi-currency support with automatic conversion
- **Order Optimization**: Broker-specific order routing and execution

## Alpaca Integration

### API Configuration

```python
# Alpaca REST API v2
import alpaca_trade_api as tradeapi

client = tradeapi.REST(
    key_id=api_key,
    secret_key=secret_key,
    base_url='https://paper-api.alpaca.markets',  # Paper trading
    api_version='v2'
)
```

### Supported Features

- **Account Management**: Portfolio value, buying power, positions
- **Market Data**: Real-time quotes for US stocks and ETFs
- **Order Management**: Market, limit, stop orders with fractional shares
- **Paper Trading**: Risk-free testing with $100,000 virtual cash

### Symbol Mapping for Global Strategy

```python
# Alpaca uses US-listed symbols and ADRs
alpaca_symbols = {
    'ASML': 'ASML',      # ASML ADR (US-listed)
    'SAP': 'SAP',        # SAP ADR (US-listed)
    'TSM': 'TSM',        # Taiwan Semi ADR
    'NVDA': 'NVDA',      # Native US listing
    'MSFT': 'MSFT'       # Native US listing
}
```

### Order Execution

```python
# Alpaca order placement
order = client.submit_order(
    symbol='NVDA',
    qty=10.5,           # Fractional shares supported
    side='buy',
    type='market',
    time_in_force='day'
)
```

## Swissquote Integration

### API Configuration

```python
# Swissquote OW Trading API (OAuth2)
from swissquote_api import SwissquoteAPI

client = SwissquoteAPI(
    client_id=oauth_client_id,
    client_secret=oauth_client_secret,
    base_url='https://api.swissquote.com/ow/v1',
    demo_mode=True  # For educational use
)
```

### Supported Features

- **Global Market Access**: US, European, Asian markets
- **Multi-Currency**: CHF, EUR, USD, GBP trading and settlement
- **Professional Orders**: Advanced order types and conditions
- **Real-time Data**: Global market data and quotes

### Symbol Mapping for Global Strategy

```python
# Swissquote uses native exchange symbols
swissquote_symbols = {
    'ASML': 'ASML.AS',   # Amsterdam Stock Exchange
    'SAP': 'SAP.DE',     # XETRA (German exchange)
    'TSM': 'TSM',        # US ADR or native Taiwan listing
    'NVDA': 'NVDA',      # US NASDAQ
    'MSFT': 'MSFT'       # US NASDAQ
}
```

### Order Execution

```python
# Swissquote order placement
order = client.place_order(
    symbol='ASML.AS',
    quantity=10.5,
    side='buy',
    order_type='market',
    time_in_force='day'
)
```

## Dynamic Broker Switching

### Frontend Implementation

```javascript
// Broker selection and switching
function switchBroker() {
    const brokerSelect = document.getElementById('brokerSelect');
    currentBroker = brokerSelect.value;
    
    // Update UI and reload data
    updateBrokerUI();
    loadStrategyInfo();
    loadAccountStatus();
}

// Broker-specific setup modals
function showBrokerSetup() {
    const modal = document.getElementById('brokerSetupModal');
    
    if (currentBroker === 'alpaca') {
        showAlpacaSetup();
    } else {
        showSwissquoteSetup();
    }
    
    modal.style.display = 'block';
}
```

### Backend API Routes

```python
@app.route('/api/test-connection', methods=['POST'])
def test_broker_connection():
    """Test connection to selected broker"""
    data = request.get_json()
    broker = data.get('broker')
    credentials = data.get('credentials')
    
    client = get_broker_client(broker, credentials)
    # Test connection and return status

@app.route('/api/calculate-orders', methods=['POST'])
def calculate_orders():
    """Calculate orders for selected broker"""
    broker = request.get_json().get('broker')
    
    # Use global strategy with broker-specific symbol mapping
    orders = global_strategy.calculate_trade_orders(
        broker_type=broker,
        portfolio_value=portfolio_value,
        allocation_percentage=allocation_pct
    )
```

## Security Implementation

### Credential Management

```javascript
// Local credential storage (browser-only)
const brokerConnections = {
    alpaca: { 
        connected: false, 
        credentials: null 
    },
    swissquote: { 
        connected: false, 
        credentials: null 
    }
};

// Secure credential handling
function connectAlpaca() {
    const credentials = {
        apiKey: document.getElementById('alpacaApiKey').value,
        secretKey: document.getElementById('alpacaSecretKey').value,
        paperMode: document.getElementById('alpacaPaperMode').checked
    };
    
    // Test connection before storing
    testBrokerConnection('alpaca', credentials)
        .then(success => {
            if (success) {
                brokerConnections.alpaca.credentials = credentials;
                brokerConnections.alpaca.connected = true;
            }
        });
}
```

### API Security

- **HTTPS Only**: All API communications encrypted
- **No Server Storage**: Credentials stored locally in browser only
- **Demo Mode Default**: Safe defaults for educational use
- **Rate Limiting**: Respect broker API rate limits
- **Error Handling**: Graceful degradation on API failures

## Error Handling and Fallbacks

### Connection Failures

```python
def get_broker_client(broker_type, credentials=None):
    """Get broker client with fallback to demo mode"""
    try:
        if broker_type == 'alpaca':
            return create_alpaca_client(credentials)
        elif broker_type == 'swissquote':
            return create_swissquote_client(credentials)
    except Exception as e:
        logger.error(f"Failed to create {broker_type} client: {e}")
        return None  # Fallback to demo mode
```

### Demo Mode Fallbacks

```python
def calculate_orders_with_fallback(broker_type, portfolio_value, allocation_pct):
    """Calculate orders with demo fallback"""
    client = get_broker_client(broker_type)
    
    if client is None:
        # Use demo mode with mock data
        return generate_demo_orders(portfolio_value, allocation_pct)
    else:
        # Use real broker API
        return calculate_real_orders(client, portfolio_value, allocation_pct)
```

## Testing and Validation

### Unit Tests

```python
def test_broker_switching():
    """Test dynamic broker switching"""
    # Test Alpaca connection
    alpaca_client = get_broker_client('alpaca', alpaca_creds)
    assert alpaca_client is not None
    
    # Test Swissquote connection
    swissquote_client = get_broker_client('swissquote', swissquote_creds)
    assert swissquote_client is not None
    
    # Test strategy consistency
    alpaca_orders = global_strategy.calculate_orders('alpaca')
    swissquote_orders = global_strategy.calculate_orders('swissquote')
    
    # Same strategy, different symbols
    assert len(alpaca_orders) == len(swissquote_orders)
```

### Integration Tests

```python
def test_end_to_end_flow():
    """Test complete broker integration flow"""
    # 1. Connect to broker
    # 2. Load strategy
    # 3. Calculate orders
    # 4. Execute demo orders
    # 5. Verify results
    pass
```

## Performance Considerations

### Caching Strategy

- **Market Data**: Cache quotes for 1-5 seconds to reduce API calls
- **Account Info**: Cache account data for 30 seconds
- **Strategy Data**: Cache strategy calculations until parameters change

### Rate Limiting

- **Alpaca**: 200 requests per minute
- **Swissquote**: Varies by endpoint and client tier
- **Implementation**: Queue requests and implement exponential backoff

### Optimization

- **Batch Requests**: Group multiple symbol quotes into single API calls
- **Lazy Loading**: Load broker data only when needed
- **Connection Pooling**: Reuse HTTP connections for better performance

## Deployment Considerations

### Environment Variables

```bash
# Optional - for default connections
ALPACA_API_KEY=your_paper_api_key
ALPACA_SECRET_KEY=your_paper_secret_key
SWISSQUOTE_CLIENT_ID=your_oauth_client_id
SWISSQUOTE_CLIENT_SECRET=your_oauth_client_secret

# Platform configuration
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com
```

### Docker Configuration

```dockerfile
# Multi-broker support
FROM python:3.11-slim

# Install broker API dependencies
RUN pip install alpaca-trade-api requests flask flask-cors

# Copy application files
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

### Monitoring and Logging

```python
import logging

# Configure logging for broker operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def log_broker_operation(broker, operation, result):
    """Log broker operations for monitoring"""
    logger.info(f"Broker: {broker}, Operation: {operation}, Result: {result}")
```

This technical documentation provides the foundation for maintaining and extending the dual-broker integration while ensuring security, performance, and reliability.

