from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import logging

logger = logging.getLogger(__name__)

# Database setup - support multiple database types
def get_database_url():
    """Get database URL based on environment configuration"""
    if Config.USE_POSTGRES:
        return Config.DATABASE_URL
    elif Config.USE_LOCAL_DB:
        return Config.LOCAL_DATABASE_URL
    else:
        return Config.IN_MEMORY_DATABASE_URL

engine = create_engine(get_database_url(), echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class AppState(Base):
    __tablename__ = 'app_state'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FormField(Base):
    __tablename__ = 'form_fields'
    
    id = Column(Integer, primary_key=True)
    object_type = Column(String(50), nullable=False)  # contact, deal, etc.
    field_name = Column(String(100), nullable=False)
    field_label = Column(String(200))
    field_type = Column(String(50))
    is_enabled = Column(String(10), default='false')  # true/false as string
    is_important = Column(String(10), default='false')  # true/false as string
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchPreference(Base):
    __tablename__ = 'search_preferences'
    
    id = Column(Integer, primary_key=True)
    object_type = Column(String(50), nullable=False)  # contacts, deals, etc.
    search_strategy = Column(String(50), nullable=False)  # email_only, customer_id_only, email_then_customer_id, customer_id_then_email
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Create default admin user if it doesn't exist
        create_default_admin()
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise e

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        from werkzeug.security import generate_password_hash
        from config import Config
        
        session = get_session()
        try:
            # Check if admin user exists
            admin_user = session.query(User).filter_by(username=Config.ADMIN_USERNAME).first()
            if not admin_user:
                # Create default admin user
                password_hash = generate_password_hash(Config.ADMIN_PASSWORD)
                admin_user = User(
                    username=Config.ADMIN_USERNAME,
                    password_hash=password_hash
                )
                session.add(admin_user)
                session.commit()
                logger.info(f"Created default admin user: {Config.ADMIN_USERNAME}")
            else:
                logger.info(f"Admin user already exists: {Config.ADMIN_USERNAME}")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error creating default admin user: {str(e)}")

def get_session():
    """Get a new database session"""
    return Session() 