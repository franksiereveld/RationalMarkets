# RationalMarkets Data Model

## Overview
This data model is based on industry standards including:
- **Redis Securities Portfolio Model** - JSON-based brokerage data structure
- **Alpaca API** - Modern trading API position structure
- **FIX Protocol** - Industry standard for securities trading

## Core Entities

### 1. Trade Strategy (Analysis)
Represents an AI-generated trade recommendation with multiple positions.

```json
{
  "id": "TRADE_001",
  "tradeName": "AI Tech Leaders",
  "tradeDescription": "Long NVDA, MSFT, GOOGL due to AI boom",
  "analysisDate": "2025-10-14T10:00:00Z",
  "userId": "USER_001",
  "status": "active",
  "positions": {
    "longs": [...],
    "shorts": [...],
    "derivatives": [...]
  },
  "summary": {
    "expectedReturn": "15-25%",
    "riskLevel": "Medium",
    "timeHorizon": "6-12 months"
  }
}
```

### 2. Position
Represents a single security position within a trade strategy.

```json
{
  "id": "POS_001",
  "tradeId": "TRADE_001",
  "ticker": "NVDA",
  "name": "NVIDIA Corporation",
  "type": "long",
  "allocation": 40.0,
  "currentPrice": 450.25,
  "marketCap": "$1.1T",
  "sixMonthReturn": 85.5,
  "chartData": [
    {"date": "2025-04-14", "price": 243.50},
    {"date": "2025-10-14", "price": 450.25}
  ],
  "financials": {
    "pe": 65.5,
    "ps": 25.3,
    "pb": 45.2,
    "evEbitda": 55.1
  },
  "rationale": "Leading AI chip manufacturer with strong growth...",
  "createdAt": "2025-10-14T10:00:00Z",
  "updatedAt": "2025-10-14T10:00:00Z"
}
```

### 3. Security Lot (for actual portfolio tracking)
When users execute trades, track individual lots similar to brokerage systems.

```json
{
  "id": "LOT_001",
  "accountNo": "ACC10001",
  "ticker": "NVDA",
  "purchaseDate": 1665082800,
  "price": 450.25,
  "quantity": 10,
  "type": "EQUITY",
  "costBasis": 4502.50,
  "currentValue": 4502.50,
  "unrealizedPL": 0.00
}
```

### 4. User Account
User profile and account information.

```json
{
  "id": "USER_001",
  "phoneNumber": "+1234567890",
  "verified": true,
  "accountNo": "ACC10001",
  "accountOpenDate": "2025-01-01",
  "accountType": "individual",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

## Database Schema (PostgreSQL)

### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    account_no VARCHAR(50) UNIQUE,
    account_open_date TIMESTAMP,
    account_type VARCHAR(20) DEFAULT 'individual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### trade_strategies
```sql
CREATE TABLE trade_strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    trade_name VARCHAR(255) NOT NULL,
    trade_description TEXT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    expected_return VARCHAR(50),
    risk_level VARCHAR(20),
    time_horizon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### positions
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trade_strategies(id),
    ticker VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    position_type VARCHAR(20) NOT NULL, -- 'long', 'short', 'derivative'
    allocation DECIMAL(5,2),
    current_price DECIMAL(10,2),
    market_cap VARCHAR(20),
    six_month_return DECIMAL(10,2),
    pe_ratio DECIMAL(10,2),
    ps_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    ev_ebitda DECIMAL(10,2),
    rationale TEXT,
    chart_data JSONB, -- Store as JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### security_lots (for actual portfolio tracking)
```sql
CREATE TABLE security_lots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_no VARCHAR(50),
    ticker VARCHAR(10) NOT NULL,
    purchase_date TIMESTAMP NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    security_type VARCHAR(20) DEFAULT 'EQUITY',
    cost_basis DECIMAL(15,2),
    current_value DECIMAL(15,2),
    unrealized_pl DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Trade Analysis
- `POST /api/analyze-trade` - Create new AI trade analysis
- `GET /api/trades` - Get all user's trade strategies
- `GET /api/trades/:id` - Get specific trade strategy
- `PUT /api/trades/:id` - Update trade strategy
- `DELETE /api/trades/:id` - Delete trade strategy

### Positions
- `GET /api/positions` - Get all positions across all trades
- `GET /api/positions/:id` - Get specific position
- `GET /api/trades/:tradeId/positions` - Get positions for a trade

### Market Data
- `GET /api/market-data/:ticker` - Get real-time market data for ticker
- `GET /api/market-data/batch` - Get data for multiple tickers

### User Management
- `POST /api/auth/send-code` - Send SMS verification code
- `POST /api/auth/verify-code` - Verify SMS code and login
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile

## Data Flow

1. **User submits trade idea** → AI analyzes → Creates trade_strategy record
2. **AI generates positions** → Creates position records linked to trade_strategy
3. **Market data fetched** → Updates position prices in real-time
4. **User executes trade** → Creates security_lot records for actual holdings
5. **Portfolio tracking** → Aggregates security_lots for portfolio view

## Key Design Principles

1. **Separation of Analysis vs Execution**
   - Trade strategies are recommendations (not executed)
   - Security lots are actual holdings (executed trades)

2. **Real-time Market Data**
   - Positions store snapshot data
   - Real-time prices fetched on demand
   - Chart data cached for performance

3. **Flexible Position Types**
   - Longs, shorts, and derivatives supported
   - Easy to extend for new asset types

4. **Audit Trail**
   - All entities have created_at/updated_at timestamps
   - Can track position changes over time

## Future Enhancements

1. **Orders Table** - Track order history and execution
2. **Transactions Table** - Record all buy/sell transactions
3. **Performance Metrics** - Calculate returns, Sharpe ratio, etc.
4. **Watchlists** - Allow users to track securities
5. **Alerts** - Price alerts and notifications
6. **Social Features** - Share trades, follow other users

