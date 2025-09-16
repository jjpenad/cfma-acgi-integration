from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import logging
import json

logger = logging.getLogger(__name__)

# Database setup - support multiple database types
def get_database_url():
    """Get database URL based on environment configuration"""
    if Config.USE_POSTGRES:
        # Handle Heroku PostgreSQL URL conversion
        # Heroku provides postgres:// but SQLAlchemy expects postgresql://
        database_url = Config.DATABASE_URL
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("Converted Heroku postgres:// URL to postgresql:// for SQLAlchemy compatibility")
        return database_url
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)

class AppState(Base):
    __tablename__ = 'app_state'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ContactFieldMapping(Base):
    __tablename__ = 'contact_field_mapping'
    id = Column(Integer, primary_key=True)
    mapping = Column(Text)  # Store JSON as text instead of PickleType

    @staticmethod
    def set_mapping(mapping):
        session = Session()
        try:
            obj = session.query(ContactFieldMapping).first()
            if not obj:
                obj = ContactFieldMapping()
            # Convert mapping to JSON string
            obj.mapping = json.dumps(mapping) if mapping else '{}'
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving mapping: {str(e)}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_mapping():
        session = Session()
        try:
            obj = session.query(ContactFieldMapping).first()
            if obj and obj.mapping:
                # Parse JSON string back to dict
                return json.loads(obj.mapping)
            return {}
        except Exception as e:
            logger.error(f"Error loading mapping: {str(e)}")
            return {}
        finally:
            session.close()


class MembershipFieldMapping(Base):
    __tablename__ = 'membership_field_mapping'
    id = Column(Integer, primary_key=True)
    mapping = Column(Text)  # Store JSON as text instead of PickleType
    
    @staticmethod
    def set_mapping(mapping):
        session = Session()
        try:
            obj = session.query(MembershipFieldMapping).first()
            if not obj:
                obj = MembershipFieldMapping()
            obj.mapping = json.dumps(mapping) if mapping else '{}'
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving mapping: {str(e)}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_mapping():
        session = Session()
        try:
            obj = session.query(MembershipFieldMapping).first()
            if obj and obj.mapping:
                # Parse JSON string back to dict
                return json.loads(obj.mapping)
            return {}
        except Exception as e:
            logger.error(f"Error loading mapping: {str(e)}")
            return {}
        finally:
            session.close()

class EventFieldMapping(Base):
    __tablename__ = 'event_field_mapping'
    id = Column(Integer, primary_key=True)
    mapping = Column(Text)  # Store JSON as text instead of PickleType
    
    @staticmethod
    def set_mapping(mapping):
        session = Session()
        try:
            obj = session.query(EventFieldMapping).first()
            if not obj:
                obj = EventFieldMapping()
            obj.mapping = json.dumps(mapping) if mapping else '{}'
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving mapping: {str(e)}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_mapping():
        session = Session()
        try:
            obj = session.query(EventFieldMapping).first()
            if obj and obj.mapping:
                # Parse JSON string back to dict
                return json.loads(obj.mapping)
            return {}
        except Exception as e:
            logger.error(f"Error loading mapping: {str(e)}")
            return {}
        finally:
            session.close()



class PurchasedProductsFieldMapping(Base):
    __tablename__ = 'purchased_products_field_mapping'
    id = Column(Integer, primary_key=True)
    mapping = Column(Text)  # Store JSON as text instead of PickleType

    @staticmethod
    def set_mapping(mapping):
        session = Session()
        try:
            obj = session.query(PurchasedProductsFieldMapping).first()
            if not obj:
                obj = PurchasedProductsFieldMapping()
            obj.mapping = json.dumps(mapping) if mapping else '{}'
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving mapping: {str(e)}")
            raise   
        finally:
            session.close()

    @staticmethod
    def get_mapping():
        session = Session()
        try:
            obj = session.query(PurchasedProductsFieldMapping).first()
            if obj and obj.mapping:
                # Parse JSON string back to dict
                return json.loads(obj.mapping)
            return {}
        except Exception as e:  
            logger.error(f"Error loading mapping: {str(e)}")
            return {}
        finally:
            session.close()

class SchedulingConfig(Base):
    __tablename__ = 'scheduling_config'
    
    id = Column(Integer, primary_key=True)
    frequency = Column(Integer, nullable=False)  # 5, 10, or 15 minutes
    enabled = Column(String(10), default='false')  # true/false as string
    customer_ids = Column(Text, nullable=False)  # Comma or newline separated customer IDs
    production_mode = Column(String(10), default='false')  # true/false as string - sync all customers from ACGI
    sync_contacts = Column(String(10), default='true')  # true/false as string
    sync_memberships = Column(String(10), default='true')  # true/false as string
    sync_orders = Column(String(10), default='true')  # true/false as string
    sync_events = Column(String(10), default='true')  # true/false as string
    last_sync = Column(DateTime)  # Last successful sync timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @staticmethod
    def get_config():
        session = Session()
        try:
            config = session.query(SchedulingConfig).first()
            if config:
                return {
                    'frequency': config.frequency,
                    'enabled': config.enabled == 'true',
                    'customer_ids': config.customer_ids,
                    'production_mode': config.production_mode == 'true',
                    'sync_contacts': config.sync_contacts == 'true',
                    'sync_memberships': config.sync_memberships == 'true',
                    'sync_purchased_products': config.sync_orders == 'true',
                    'sync_events': config.sync_events == 'true',
                    'last_sync': config.last_sync.isoformat() if config.last_sync else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting scheduling config: {str(e)}")
            return None
        finally:
            session.close()

    @staticmethod
    def save_config(config_data):
        session = Session()
        try:
            config = session.query(SchedulingConfig).first()
            if not config:
                config = SchedulingConfig()
            
            config.frequency = config_data.get('frequency')
            config.enabled = str(config_data.get('enabled', False)).lower()
            config.customer_ids = config_data.get('customer_ids', '')
            config.production_mode = str(config_data.get('production_mode', False)).lower()
            config.sync_contacts = str(config_data.get('sync_contacts', True)).lower()
            config.sync_memberships = str(config_data.get('sync_memberships', True)).lower()
            config.sync_orders = str(config_data.get('sync_purchased_products', True)).lower()
            config.sync_events = str(config_data.get('sync_events', True)).lower()
            
            session.add(config)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving scheduling config: {str(e)}")
            return False
        finally:
            session.close()

    @staticmethod
    def update_last_sync():
        session = Session()
        try:
            config = session.query(SchedulingConfig).first()
            if config:
                config.last_sync = datetime.now(timezone.utc)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating last sync: {str(e)}")
        finally:
            session.close()

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Checking database tables...")
        
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            logger.info(f"Tables already exist: {existing_tables}")
            logger.info("Skipping table creation - tables already present")
        else:
            logger.info("Creating database tables...")
            Base.metadata.create_all(engine)
            logger.info("Database tables created successfully")
        
        # Always create default admin user if it doesn't exist
        create_default_admin()
        
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        # Don't raise the error - just log it and continue
        # This allows the app to start even if there are database issues
        logger.warning("Continuing with application startup despite database error")

def reset_db():
    """Reset database - drop all tables and recreate them"""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(engine)
        logger.info("All tables dropped successfully")
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables recreated successfully")
        
        # Create default admin user
        create_default_admin()
        
        logger.info("Database reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

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
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error in create_default_admin: {str(e)}")

def get_session():
    """Get a new database session"""
    return Session()

def get_app_credentials():
    """Get application credentials from AppState"""
    session = get_session()
    try:
        # Get ACGI credentials
        acgi_username = session.query(AppState).filter_by(key='acgi_username').first()
        acgi_password = session.query(AppState).filter_by(key='acgi_password').first()
        acgi_environment = session.query(AppState).filter_by(key='acgi_environment').first()
        
        # Get HubSpot API keys for different object types
        hubspot_api_key = session.query(AppState).filter_by(key='hubspot_api_key').first()
        hubspot_api_key_contacts = session.query(AppState).filter_by(key='hubspot_api_key_contacts').first()
        hubspot_api_key_memberships = session.query(AppState).filter_by(key='hubspot_api_key_memberships').first()
        hubspot_api_key_orders = session.query(AppState).filter_by(key='hubspot_api_key_orders').first()
        hubspot_api_key_events = session.query(AppState).filter_by(key='hubspot_api_key_events').first()
        
        if not all([acgi_username, acgi_password]):
            return None
        
        # Use specific API keys if available, fallback to general one
        credentials = {
            'acgi_username': acgi_username.value,
            'acgi_password': acgi_password.value,
            'acgi_environment': acgi_environment.value if acgi_environment else 'test',
            'hubspot_api_key': hubspot_api_key.value if hubspot_api_key else None,
            'hubspot_api_key_contacts': hubspot_api_key_contacts.value if hubspot_api_key_contacts else hubspot_api_key.value if hubspot_api_key else None,
            'hubspot_api_key_memberships': hubspot_api_key_memberships.value if hubspot_api_key_memberships else hubspot_api_key.value if hubspot_api_key else None,
            'hubspot_api_key_orders': hubspot_api_key_orders.value if hubspot_api_key_orders else hubspot_api_key.value if hubspot_api_key else None,
            'hubspot_api_key_events': hubspot_api_key_events.value if hubspot_api_key_events else hubspot_api_key.value if hubspot_api_key else None
        }
        
        # Ensure at least one HubSpot API key is available
        if not any([credentials['hubspot_api_key'], credentials['hubspot_api_key_contacts'], 
                   credentials['hubspot_api_key_memberships'], credentials['hubspot_api_key_orders'], 
                   credentials['hubspot_api_key_events']]):
            return None
            
        return credentials
    except Exception as e:
        logger.error(f"Error getting app credentials: {str(e)}")
        return None
    finally:
        session.close() 