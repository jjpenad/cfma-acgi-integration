from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from functools import wraps
from models import get_session, User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        try:
            db_session = get_session()
            try:
                user = db_session.query(User).filter_by(username=username).first()
                
                if user and check_password_hash(user.password_hash, password):
                    # Update last login
                    user.last_login = datetime.utcnow()
                    db_session.commit()
                    
                    # Set session
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session.permanent = True
                    
                    logger.info(f"User {username} logged in successfully")
                    flash('Login successful!', 'success')
                    return redirect(url_for('main.index'))
                else:
                    logger.warning(f"Failed login attempt for username: {username}")
                    flash('Invalid username or password', 'error')
            finally:
                db_session.close()
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    if 'username' in session:
        logger.info(f"User {session['username']} logged out")
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def index():
    """Redirect root to login if not authenticated"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    return redirect(url_for('auth.login')) 