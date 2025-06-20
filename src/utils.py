import logging
from models import get_session, AppState

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_app_credentials():
    """Get credentials from AppState database with error handling"""
    try:
        session = get_session()
        try:
            creds = {s.key: s.value for s in session.query(AppState).all()}
            return creds
        except Exception as e:
            logger.error(f"Error querying AppState: {str(e)}")
            return {}
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        return {}

def save_credentials(credentials_dict):
    """Save credentials to AppState database with error handling"""
    try:
        session = get_session()
        try:
            for key, value in credentials_dict.items():
                if value is not None:
                    state = session.query(AppState).filter_by(key=key).first()
                    if state:
                        state.value = value
                    else:
                        session.add(AppState(key=key, value=value))
            session.commit()
            logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving credentials: {str(e)}")
            raise e
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting session for saving credentials: {str(e)}")
        raise e 