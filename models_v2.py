"""
RationalMarkets Database Models
Based on industry standards (FIX Protocol, ISO 20022, brokerage best practices)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()


class User(db.Model):
    """User/Investor entity"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    phone_verified = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'phoneVerified': self.phone_verified,
            'name': self.name,
            'email': self.email,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }


class Portfolio(db.Model):
    """Portfolio/Account entity"""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trades = db.relationship('Trade', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    positions = db.relationship('Position', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'name': self.name,
            'currency': self.currency,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class Trade(db.Model):
    """Trade (AI Analysis) entity"""
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    trade_name = db.Column(db.String(255), nullable=False)
    trade_description = db.Column(db.Text)
    recommendation = db.Column(db.String(50))  # RECOMMENDED, CONDITIONAL, NOT_RECOMMENDED
    risk_level = db.Column(db.String(20))  # LOW, MODERATE, HIGH, VERY_HIGH
    ai_rationale = db.Column(db.Text)
    return_estimates = db.Column(JSONB)  # {"1M": "5.2%", "3M": "12.5%", ...}
    status = db.Column(db.String(20), default='active', index=True)  # draft, active, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = db.relationship('Position', backref='trade', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'portfolioId': self.portfolio_id,
            'tradeName': self.trade_name,
            'tradeDescription': self.trade_description,
            'recommendation': self.recommendation,
            'riskLevel': self.risk_level,
            'aiRationale': self.ai_rationale,
            'returnEstimates': self.return_estimates,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'positions': [p.to_dict() for p in self.positions]
        }


class Position(db.Model):
    """Position (Security Lot) entity"""
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    ticker = db.Column(db.String(20), nullable=False, index=True)
    security_name = db.Column(db.String(255))
    security_type = db.Column(db.String(50))  # equity, fixed_income, index, future, option, crypto
    position_type = db.Column(db.String(10))  # long, short
    allocation = db.Column(db.Numeric(5, 2))  # Percentage allocation (e.g., 30.00)
    quantity = db.Column(db.Numeric(18, 8), default=0)  # Number of shares/contracts
    entry_price = db.Column(db.Numeric(18, 2))  # Average entry price
    entry_date = db.Column(db.DateTime)
    current_price = db.Column(db.Numeric(18, 2))  # Latest market price
    market_value = db.Column(db.Numeric(18, 2))  # Current market value
    unrealized_pnl = db.Column(db.Numeric(18, 2))  # Unrealized profit/loss
    realized_pnl = db.Column(db.Numeric(18, 2))  # Realized profit/loss
    status = db.Column(db.String(20), default='recommended', index=True)  # recommended, active, closed
    rationale = db.Column(db.Text)  # AI rationale for this position
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='position', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tradeId': self.trade_id,
            'portfolioId': self.portfolio_id,
            'ticker': self.ticker,
            'securityName': self.security_name,
            'securityType': self.security_type,
            'positionType': self.position_type,
            'allocation': float(self.allocation) if self.allocation else None,
            'quantity': float(self.quantity) if self.quantity else 0,
            'entryPrice': float(self.entry_price) if self.entry_price else None,
            'entryDate': self.entry_date.isoformat() if self.entry_date else None,
            'currentPrice': float(self.current_price) if self.current_price else None,
            'marketValue': float(self.market_value) if self.market_value else None,
            'unrealizedPnL': float(self.unrealized_pnl) if self.unrealized_pnl else None,
            'realizedPnL': float(self.realized_pnl) if self.realized_pnl else None,
            'status': self.status,
            'rationale': self.rationale,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class Transaction(db.Model):
    """Transaction (Execution Record) entity"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    ticker = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy, sell, short, cover, dividend, split, spinoff
    quantity = db.Column(db.Numeric(18, 8), nullable=False)
    price = db.Column(db.Numeric(18, 2), nullable=False)
    amount = db.Column(db.Numeric(18, 2), nullable=False)  # Total transaction amount
    fees = db.Column(db.Numeric(18, 2), default=0)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'positionId': self.position_id,
            'portfolioId': self.portfolio_id,
            'ticker': self.ticker,
            'transactionType': self.transaction_type,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'amount': float(self.amount),
            'fees': float(self.fees),
            'transactionDate': self.transaction_date.isoformat() if self.transaction_date else None,
            'notes': self.notes
        }


class Security(db.Model):
    """Security Master entity"""
    __tablename__ = 'securities'
    
    ticker = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    security_type = db.Column(db.String(50), index=True)
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(3))
    isin = db.Column(db.String(12))  # International Securities Identification Number
    sector = db.Column(db.String(100), index=True)
    industry = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'ticker': self.ticker,
            'name': self.name,
            'securityType': self.security_type,
            'exchange': self.exchange,
            'currency': self.currency,
            'isin': self.isin,
            'sector': self.sector,
            'industry': self.industry,
            'active': self.active,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None
        }

