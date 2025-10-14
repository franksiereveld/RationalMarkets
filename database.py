"""
Database connection and session management for RationalMarkets
Supports both PostgreSQL (production) and SQLite (development)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from models import Base
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self, database_url=None):
        """
        Initialize database connection
        
        Args:
            database_url: Database connection string. If None, reads from environment.
                         Format: postgresql://user:pass@host:port/dbname
                         or: sqlite:///path/to/database.db
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        
        # Default to SQLite for development
        if not self.database_url:
            self.database_url = 'sqlite:///rationalmarkets.db'
            logger.warning("No DATABASE_URL found, using SQLite: rationalmarkets.db")
        
        # Fix Heroku/Railway postgres:// to postgresql://
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        # Create engine
        self.engine = self._create_engine()
        
        # Create session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def _create_engine(self):
        """Create SQLAlchemy engine with appropriate settings"""
        
        if self.database_url.startswith('sqlite'):
            # SQLite settings
            engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL logging
                connect_args={'check_same_thread': False}
            )
            logger.info(f"Connected to SQLite database")
        else:
            # PostgreSQL settings
            engine = create_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600  # Recycle connections after 1 hour
            )
            logger.info(f"Connected to PostgreSQL database")
        
        return engine
    
    def create_all_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def drop_all_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
            return True
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            return False
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close_session(self):
        """Close the current session"""
        self.Session.remove()
    
    def health_check(self):
        """Check if database connection is healthy"""
        try:
            session = self.get_session()
            from sqlalchemy import text
            session.execute(text('SELECT 1'))
            session.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
_db_instance = None


def get_database():
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_database(database_url=None):
    """Initialize database and create tables"""
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.create_all_tables()
    return _db_instance


# Context manager for database sessions
class DatabaseSession:
    """Context manager for database sessions"""
    
    def __init__(self, db=None):
        self.db = db or get_database()
        self.session = None
    
    def __enter__(self):
        self.session = self.db.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


# Helper functions for common database operations
def get_or_create(session, model, defaults=None, **kwargs):
    """
    Get an existing record or create a new one
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        defaults: Dict of default values for new record
        **kwargs: Filter criteria
    
    Returns:
        Tuple of (instance, created) where created is True if new record was created
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict(kwargs)
        if defaults:
            params.update(defaults)
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def bulk_insert(session, model, data_list):
    """
    Bulk insert records
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        data_list: List of dicts with record data
    
    Returns:
        Number of records inserted
    """
    try:
        objects = [model(**data) for data in data_list]
        session.bulk_save_objects(objects)
        session.flush()
        return len(objects)
    except Exception as e:
        logger.error(f"Bulk insert error: {e}")
        raise


# Database migration helper
def check_database_version():
    """Check if database schema is up to date"""
    # TODO: Implement proper migration system (Alembic)
    pass


if __name__ == '__main__':
    # Test database connection
    logging.basicConfig(level=logging.INFO)
    
    print("Testing database connection...")
    db = init_database()
    
    if db.health_check():
        print("✅ Database connection successful!")
        print(f"Database URL: {db.database_url}")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nTables created: {', '.join(tables)}")
    else:
        print("❌ Database connection failed!")

