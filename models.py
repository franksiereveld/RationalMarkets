"""
Database models for RationalMarkets platform
Uses SQLAlchemy ORM for database operations
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    trades = db.relationship('Trade', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.phone_number}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'phoneNumber': self.phone_number,
            'createdAt': self.created_at.isoformat(),
            'lastLogin': self.last_login.isoformat(),
            'isActive': self.is_active
        }


class Trade(db.Model):
    """Trade analysis model"""
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Trade details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    recommendation = db.Column(db.String(50))  # RECOMMENDED, NEUTRAL, NOT_RECOMMENDED
    risk_level = db.Column(db.String(50))  # LOW, MODERATE, HIGH
    
    # AI Analysis
    analysis_text = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    long_positions = db.relationship('Position', 
                                    foreign_keys='Position.trade_id',
                                    primaryjoin="and_(Trade.id==Position.trade_id, Position.position_type=='long')",
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    short_positions = db.relationship('Position',
                                     foreign_keys='Position.trade_id', 
                                     primaryjoin="and_(Trade.id==Position.trade_id, Position.position_type=='short')",
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trade {self.name}>'
    
    def to_dict(self, include_positions=True):
        """Convert trade to dictionary"""
        result = {
            'id': self.id,
            'userId': self.user_id,
            'name': self.name,
            'description': self.description,
            'recommendation': self.recommendation,
            'riskLevel': self.risk_level,
            'analysisText': self.analysis_text,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
        
        if include_positions:
            result['longPositions'] = [pos.to_dict() for pos in self.long_positions.all()]
            result['shortPositions'] = [pos.to_dict() for pos in self.short_positions.all()]
        
        return result


class Position(db.Model):
    """Stock position model (long or short)"""
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False, index=True)
    
    # Position details
    ticker = db.Column(db.String(10), nullable=False, index=True)
    company_name = db.Column(db.String(200))
    position_type = db.Column(db.String(10), nullable=False)  # 'long' or 'short'
    allocation_percentage = db.Column(db.Float)  # 0-100
    
    # Rationale
    rationale = db.Column(db.Text)
    
    # Financial data (stored as JSON for flexibility)
    financial_data = db.Column(JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Position {self.ticker} ({self.position_type})>'
    
    def to_dict(self):
        """Convert position to dictionary"""
        return {
            'id': self.id,
            'tradeId': self.trade_id,
            'ticker': self.ticker,
            'companyName': self.company_name,
            'positionType': self.position_type,
            'allocationPercentage': self.allocation_percentage,
            'rationale': self.rationale,
            'financialData': self.financial_data,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }


# Database initialization function
def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully")


# Helper functions for database operations
def get_user_by_phone(phone_number):
    """Get user by phone number"""
    return User.query.filter_by(phone_number=phone_number).first()


def create_user(phone_number):
    """Create a new user"""
    user = User(phone_number=phone_number)
    db.session.add(user)
    db.session.commit()
    return user


def get_or_create_user(phone_number):
    """Get existing user or create new one"""
    user = get_user_by_phone(phone_number)
    if not user:
        user = create_user(phone_number)
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
    return user


def get_user_trades(user_id, limit=50, offset=0):
    """Get trades for a user with pagination"""
    return Trade.query.filter_by(user_id=user_id)\
                     .order_by(Trade.created_at.desc())\
                     .limit(limit)\
                     .offset(offset)\
                     .all()


def get_trade_by_id(trade_id, user_id=None):
    """Get trade by ID, optionally filtered by user"""
    query = Trade.query.filter_by(id=trade_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    return query.first()


def create_trade(user_id, name, description, recommendation, risk_level, analysis_text):
    """Create a new trade"""
    trade = Trade(
        user_id=user_id,
        name=name,
        description=description,
        recommendation=recommendation,
        risk_level=risk_level,
        analysis_text=analysis_text
    )
    db.session.add(trade)
    db.session.commit()
    return trade


def create_position(trade_id, ticker, company_name, position_type, 
                   allocation_percentage, rationale, financial_data):
    """Create a new position"""
    position = Position(
        trade_id=trade_id,
        ticker=ticker,
        company_name=company_name,
        position_type=position_type,
        allocation_percentage=allocation_percentage,
        rationale=rationale,
        financial_data=financial_data
    )
    db.session.add(position)
    db.session.commit()
    return position


def delete_trade(trade_id, user_id):
    """Delete a trade (and its positions via cascade)"""
    trade = get_trade_by_id(trade_id, user_id)
    if trade:
        db.session.delete(trade)
        db.session.commit()
        return True
    return False

