"""
SQLAlchemy Database Models for RationalMarkets
Implements user authentication, trades, portfolios, and securities tracking
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Numeric, Boolean, DateTime, Text,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User accounts with phone-based authentication"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    
    # Authentication
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(10))
    verification_expires_at = Column(DateTime)
    
    # Preferences
    preferences = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    broker_connections = relationship("BrokerConnection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.phone_number}>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'phoneNumber': self.phone_number,
            'email': self.email,
            'fullName': self.full_name,
            'isVerified': self.is_verified,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }


class Security(Base):
    """Master table for all tradeable securities"""
    __tablename__ = 'securities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    security_type = Column(String(50), nullable=False, index=True)
    
    # Identifiers
    exchange = Column(String(50))
    currency = Column(String(10), default='USD')
    country = Column(String(50))
    
    # Classification
    sector = Column(String(100), index=True)
    industry = Column(String(100))
    description = Column(Text)
    
    # Market data (cached)
    current_price = Column(Numeric(20, 6))
    market_cap = Column(BigInteger)
    volume = Column(BigInteger)
    avg_volume = Column(BigInteger)
    
    # Fundamental data
    pe_ratio = Column(Numeric(10, 2))
    ps_ratio = Column(Numeric(10, 2))
    pb_ratio = Column(Numeric(10, 2))
    ev_ebitda = Column(Numeric(10, 2))
    dividend_yield = Column(Numeric(10, 4))
    
    # Price ranges
    fifty_two_week_high = Column(Numeric(20, 6))
    fifty_two_week_low = Column(Numeric(20, 6))
    
    # Metadata
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_source = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="security")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="security")
    price_history = relationship("PriceHistory", back_populates="security", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('ticker', 'exchange', name='uq_ticker_exchange'),
    )
    
    def __repr__(self):
        return f"<Security {self.ticker}>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'ticker': self.ticker,
            'name': self.name,
            'securityType': self.security_type,
            'exchange': self.exchange,
            'currency': self.currency,
            'sector': self.sector,
            'industry': self.industry,
            'currentPrice': float(self.current_price) if self.current_price else None,
            'marketCap': self.market_cap,
            'peRatio': float(self.pe_ratio) if self.pe_ratio else None,
            'psRatio': float(self.ps_ratio) if self.ps_ratio else None,
            'pbRatio': float(self.pb_ratio) if self.pb_ratio else None
        }


class Trade(Base):
    """AI-generated trade strategies and recommendations"""
    __tablename__ = 'trades'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Trade metadata
    trade_name = Column(String(255), nullable=False)
    trade_description = Column(Text, nullable=False)
    status = Column(String(50), default='draft', index=True)
    
    # AI analysis
    ai_rationale = Column(Text)
    recommendation = Column(String(50))
    risk_level = Column(String(50))
    
    # Return estimates
    return_1m = Column(Numeric(10, 4))
    return_3m = Column(Numeric(10, 4))
    return_6m = Column(Numeric(10, 4))
    return_1y = Column(Numeric(10, 4))
    return_3y = Column(Numeric(10, 4))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime)
    activated_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    positions = relationship("Position", back_populates="trade", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trade {self.trade_name}>"
    
    def to_dict(self, include_positions=True):
        # Get owner name from user relationship
        owner_name = None
        try:
            if self.user:
                # Prefer full_name, fallback to phone_number
                owner_name = self.user.full_name or self.user.phone_number
        except Exception:
            # User relationship not loaded
            pass
        
        result = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'owner': owner_name,
            'trade_name': self.trade_name,
            'trade_description': self.trade_description,
            'status': self.status,
            'ai_rationale': self.ai_rationale,
            'recommendation': self.recommendation,
            'risk_level': self.risk_level,
            'return_1m': float(self.return_1m) if self.return_1m else None,
            'return_3m': float(self.return_3m) if self.return_3m else None,
            'return_6m': float(self.return_6m) if self.return_6m else None,
            'return_1y': float(self.return_1y) if self.return_1y else None,
            'return_3y': float(self.return_3y) if self.return_3y else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }
        
        if include_positions:
            longs = [p.to_dict() for p in self.positions if p.position_type == 'long']
            shorts = [p.to_dict() for p in self.positions if p.position_type == 'short']
            derivatives = [p.to_dict() for p in self.positions if p.security_type in ['option', 'future']]
            result['longs'] = longs
            result['shorts'] = shorts
            result['derivatives'] = derivatives
        
        return result


class Position(Base):
    """Individual positions within a trade"""
    __tablename__ = 'positions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey('trades.id', ondelete='CASCADE'), nullable=False, index=True)
    security_id = Column(UUID(as_uuid=True), ForeignKey('securities.id'), nullable=False, index=True)
    
    # Position details
    position_type = Column(String(50), nullable=False, index=True)
    security_type = Column(String(50), nullable=False)
    allocation_percent = Column(Numeric(5, 2), nullable=False)
    
    # AI rationale
    rationale = Column(Text)
    
    # Execution details
    quantity = Column(Numeric(20, 6))
    entry_price = Column(Numeric(20, 6))
    current_price = Column(Numeric(20, 6))
    market_value = Column(Numeric(20, 2))
    unrealized_pnl = Column(Numeric(20, 2))
    
    # Status
    status = Column(String(50), default='recommended')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    opened_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Relationships
    trade = relationship("Trade", back_populates="positions")
    security = relationship("Security", back_populates="positions")
    
    __table_args__ = (
        CheckConstraint('allocation_percent > 0 AND allocation_percent <= 100', name='valid_allocation'),
    )
    
    def __repr__(self):
        return f"<Position {self.position_type} {self.security.ticker if self.security else 'N/A'}>"
    
    def to_dict(self):
        # Safely access security attributes
        ticker = None
        name = None
        try:
            if self.security:
                ticker = self.security.ticker
                name = self.security.name
        except Exception:
            # Security relationship not loaded or error accessing it
            pass
        
        return {
            'id': str(self.id),
            'trade_id': str(self.trade_id),
            'ticker': ticker,
            'name': name,
            'position_type': self.position_type,
            'security_type': self.security_type,
            'allocation': str(self.allocation_percent) + '%' if self.allocation_percent else None,
            'rationale': self.rationale,
            'quantity': float(self.quantity) if self.quantity else None,
            'entryPrice': float(self.entry_price) if self.entry_price else None,
            'currentPrice': float(self.current_price) if self.current_price else None,
            'marketValue': float(self.market_value) if self.market_value else None,
            'status': self.status
        }


class Portfolio(Base):
    """User's actual portfolio holdings"""
    __tablename__ = 'portfolios'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Portfolio metadata
    name = Column(String(255), nullable=False)
    broker = Column(String(50), index=True)
    broker_account_id = Column(String(255))
    currency = Column(String(10), default='USD')
    
    # Portfolio values
    total_value = Column(Numeric(20, 2))
    cash_balance = Column(Numeric(20, 2))
    equity_value = Column(Numeric(20, 2))
    
    # Performance
    total_return = Column(Numeric(10, 4))
    day_return = Column(Numeric(10, 4))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_synced_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio {self.name}>"


class PortfolioHolding(Base):
    """Actual positions held in portfolio"""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    security_id = Column(UUID(as_uuid=True), ForeignKey('securities.id'), nullable=False, index=True)
    
    # Holding details
    quantity = Column(Numeric(20, 6), nullable=False)
    average_entry_price = Column(Numeric(20, 6), nullable=False)
    current_price = Column(Numeric(20, 6))
    market_value = Column(Numeric(20, 2))
    
    # P&L
    cost_basis = Column(Numeric(20, 2))
    unrealized_pnl = Column(Numeric(20, 2))
    unrealized_pnl_percent = Column(Numeric(10, 4))
    
    # Position type
    side = Column(String(10), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    security = relationship("Security", back_populates="portfolio_holdings")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'security_id', 'side', name='uq_portfolio_security_side'),
    )


class PriceHistory(Base):
    """Historical price data for securities"""
    __tablename__ = 'price_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    security_id = Column(UUID(as_uuid=True), ForeignKey('securities.id', ondelete='CASCADE'), nullable=False)
    
    # OHLCV data
    date = Column(Date, nullable=False)
    open = Column(Numeric(20, 6))
    high = Column(Numeric(20, 6))
    low = Column(Numeric(20, 6))
    close = Column(Numeric(20, 6), nullable=False)
    volume = Column(BigInteger)
    
    # Metadata
    data_source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security = relationship("Security", back_populates="price_history")
    
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_security_date'),
        Index('idx_price_history_security_date', 'security_id', 'date'),
    )


class BrokerConnection(Base):
    """Stores broker API credentials and connection status"""
    __tablename__ = 'broker_connections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('portfolios.id', ondelete='SET NULL'))
    
    # Broker details
    broker = Column(String(50), nullable=False)
    broker_account_id = Column(String(255))
    
    # API credentials (encrypted)
    api_key_encrypted = Column(Text)
    api_secret_encrypted = Column(Text)
    access_token_encrypted = Column(Text)
    
    # Connection status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_connected_at = Column(DateTime)
    last_sync_at = Column(DateTime)
    
    # Permissions
    can_read = Column(Boolean, default=True)
    can_trade = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="broker_connections")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'broker', 'broker_account_id', name='uq_user_broker_account'),
    )

