# RationalMarkets Database Schema

## Overview

This schema supports user authentication, trade management, portfolio tracking, and securities data following industry standards (inspired by Alpaca, Redis Securities Model, and FIX protocol).

## Core Entities

### 1. Users
Stores user account information and authentication data.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    verification_code VARCHAR(10),
    verification_expires_at TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_email ON users(email);
```

### 2. Securities
Master table for all tradeable securities (stocks, bonds, options, futures, indices).

```sql
CREATE TABLE securities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    security_type VARCHAR(50) NOT NULL, -- equity, bond, option, future, index, etf, crypto
    exchange VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    country VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    
    -- Market data (cached, updated periodically)
    current_price DECIMAL(20, 6),
    market_cap BIGINT,
    volume BIGINT,
    avg_volume BIGINT,
    
    -- Fundamental data
    pe_ratio DECIMAL(10, 2),
    ps_ratio DECIMAL(10, 2),
    pb_ratio DECIMAL(10, 2),
    ev_ebitda DECIMAL(10, 2),
    dividend_yield DECIMAL(10, 4),
    
    -- Price ranges
    fifty_two_week_high DECIMAL(20, 6),
    fifty_two_week_low DECIMAL(20, 6),
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50), -- yfinance, fmp, tradier, ibkr
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker, exchange)
);

CREATE INDEX idx_securities_ticker ON securities(ticker);
CREATE INDEX idx_securities_type ON securities(security_type);
CREATE INDEX idx_securities_sector ON securities(sector);
```

### 3. Trades (AI-Generated Strategies)
Stores user's trade ideas and AI-generated recommendations.

```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Trade metadata
    trade_name VARCHAR(255) NOT NULL,
    trade_description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, closed, archived
    
    -- AI analysis
    ai_rationale TEXT,
    recommendation VARCHAR(50), -- RECOMMENDED, CONDITIONAL, NOT_RECOMMENDED
    risk_level VARCHAR(50), -- LOW, MODERATE, HIGH
    
    -- Return estimates
    return_1m DECIMAL(10, 4),
    return_3m DECIMAL(10, 4),
    return_6m DECIMAL(10, 4),
    return_1y DECIMAL(10, 4),
    return_3y DECIMAL(10, 4),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP,
    activated_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_created ON trades(created_at DESC);
```

### 4. Positions
Individual positions within a trade (longs, shorts, derivatives).

```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(id),
    
    -- Position details
    position_type VARCHAR(50) NOT NULL, -- long, short
    security_type VARCHAR(50) NOT NULL, -- equity, option, future, bond, index
    allocation_percent DECIMAL(5, 2) NOT NULL, -- e.g., 25.00 for 25%
    
    -- AI rationale
    rationale TEXT,
    
    -- Execution details (when actually traded)
    quantity DECIMAL(20, 6),
    entry_price DECIMAL(20, 6),
    current_price DECIMAL(20, 6),
    market_value DECIMAL(20, 2),
    unrealized_pnl DECIMAL(20, 2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'recommended', -- recommended, open, closed
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    CONSTRAINT valid_allocation CHECK (allocation_percent > 0 AND allocation_percent <= 100)
);

CREATE INDEX idx_positions_trade ON positions(trade_id);
CREATE INDEX idx_positions_security ON positions(security_id);
CREATE INDEX idx_positions_type ON positions(position_type);
```

### 5. Portfolios
User's actual portfolio holdings (connected to broker accounts).

```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Portfolio metadata
    name VARCHAR(255) NOT NULL,
    broker VARCHAR(50), -- alpaca, swissquote, ibkr, tradier, manual
    broker_account_id VARCHAR(255),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Portfolio values
    total_value DECIMAL(20, 2),
    cash_balance DECIMAL(20, 2),
    equity_value DECIMAL(20, 2),
    
    -- Performance
    total_return DECIMAL(10, 4),
    day_return DECIMAL(10, 4),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_connected BOOLEAN DEFAULT false, -- broker connection status
    last_synced_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolios_user ON portfolios(user_id);
CREATE INDEX idx_portfolios_broker ON portfolios(broker);
```

### 6. Portfolio Holdings
Actual positions held in user's portfolio.

```sql
CREATE TABLE portfolio_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(id),
    
    -- Holding details
    quantity DECIMAL(20, 6) NOT NULL,
    average_entry_price DECIMAL(20, 6) NOT NULL,
    current_price DECIMAL(20, 6),
    market_value DECIMAL(20, 2),
    
    -- P&L
    cost_basis DECIMAL(20, 2),
    unrealized_pnl DECIMAL(20, 2),
    unrealized_pnl_percent DECIMAL(10, 4),
    
    -- Position type
    side VARCHAR(10) NOT NULL, -- long, short
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    
    UNIQUE(portfolio_id, security_id, side)
);

CREATE INDEX idx_holdings_portfolio ON portfolio_holdings(portfolio_id);
CREATE INDEX idx_holdings_security ON portfolio_holdings(security_id);
```

### 7. Price History
Historical price data for securities.

```sql
CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
    
    -- OHLCV data
    date DATE NOT NULL,
    open DECIMAL(20, 6),
    high DECIMAL(20, 6),
    low DECIMAL(20, 6),
    close DECIMAL(20, 6) NOT NULL,
    volume BIGINT,
    
    -- Metadata
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(security_id, date)
);

CREATE INDEX idx_price_history_security_date ON price_history(security_id, date DESC);
```

### 8. Broker Connections
Stores broker API credentials and connection status.

```sql
CREATE TABLE broker_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE SET NULL,
    
    -- Broker details
    broker VARCHAR(50) NOT NULL, -- alpaca, swissquote, ibkr, tradier
    broker_account_id VARCHAR(255),
    
    -- API credentials (encrypted)
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    access_token_encrypted TEXT,
    
    -- Connection status
    is_active BOOLEAN DEFAULT true,
    is_connected BOOLEAN DEFAULT false,
    last_connected_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    
    -- Permissions
    can_read BOOLEAN DEFAULT true,
    can_trade BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, broker, broker_account_id)
);

CREATE INDEX idx_broker_connections_user ON broker_connections(user_id);
```

## Relationships

```
users (1) ──→ (N) trades
users (1) ──→ (N) portfolios
users (1) ──→ (N) broker_connections

trades (1) ──→ (N) positions
positions (N) ──→ (1) securities

portfolios (1) ──→ (N) portfolio_holdings
portfolio_holdings (N) ──→ (1) securities

securities (1) ──→ (N) price_history
```

## Data Model Features

### Industry Standard Compliance
- **Alpaca-inspired**: Portfolio and holdings structure
- **Redis Securities Model**: Security entity design
- **FIX Protocol concepts**: Position types and security classifications

### Key Design Decisions

1. **UUID Primary Keys**: Better for distributed systems and security
2. **JSONB for Flexibility**: User preferences stored as JSON for extensibility
3. **Soft Deletes**: `is_active` flags instead of hard deletes
4. **Audit Trails**: `created_at`, `updated_at` on all tables
5. **Decimal for Money**: Avoid floating-point precision issues
6. **Broker Agnostic**: Support multiple brokers per user
7. **Separate Trades vs Portfolios**: AI recommendations vs actual holdings

### Security Considerations

1. **Encrypted Credentials**: Broker API keys stored encrypted
2. **Phone Verification**: Primary authentication method
3. **JWT Tokens**: Stateless authentication
4. **Cascade Deletes**: Proper cleanup when users delete accounts

## Next Steps

1. Create database migration scripts
2. Implement SQLAlchemy models
3. Add database connection pooling
4. Set up PostgreSQL on Railway
5. Create seed data for testing

