from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from utils import get_app_credentials, save_credentials, setup_logging
from services.acgi_client import ACGIClient
from services.hubspot_client import HubSpotClient
from services.data_mapper import DataMapper
from services.integration_service import IntegrationService
from routes.auth import login_required

logger = setup_logging()

# Initialize services
integration_service = IntegrationService()
acgi_client = ACGIClient()
hubspot_client = HubSpotClient()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html', username=session.get('username'))

@main_bp.route('/acgi-to-hubspot')
@login_required
def acgi_to_hubspot():
    """ACGI to HubSpot field mapping page"""
    return render_template('acgi_to_hubspot.html', username=session.get('username'))

@main_bp.route('/memberships')
@login_required
def memberships():
    """Memberships page"""
    return render_template('memberships.html', username=session.get('username'))

def init_routes(app):
    """Initialize main routes"""
    
    @app.route('/')
    def root():
        """Redirect root to dashboard if authenticated, otherwise to login"""
        if 'user_id' in session:
            return redirect(url_for('main.index'))
        return redirect(url_for('auth.login'))
    
    @app.route('/save-credentials', methods=['POST'])
    @login_required
    def save_credentials_route():
        """Save API credentials"""
        try:
            data = request.get_json()
            credentials = {
                'acgi_username': data.get('acgi_username', ''),
                'acgi_password': data.get('acgi_password', ''),
                'acgi_environment': data.get('acgi_environment', 'test'),
                'hubspot_api_key': data.get('hubspot_api_key', '')
            }
            
            # Save credentials
            save_credentials(credentials)
            
            return jsonify({'success': True, 'message': 'Credentials saved successfully'})
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/test-acgi', methods=['POST'])
    @login_required
    def test_acgi():
        """Test ACGI credentials"""
        try:
            creds = get_app_credentials()
            username = creds.get('acgi_username')
            password = creds.get('acgi_password')
            environment = creds.get('acgi_environment', 'test')
            
            if not username or not password:
                return jsonify({'success': False, 'message': 'ACGI credentials not configured'})
            
            # Test ACGI connection
            result = acgi_client.test_credentials({
                'userid': username, 
                'password': password,
                'environment': environment
            })
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error testing ACGI: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/test-hubspot', methods=['POST'])
    @login_required
    def test_hubspot():
        """Test HubSpot credentials"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            
            if not api_key:
                return jsonify({'success': False, 'message': 'HubSpot API key not configured'})
            
            # Test HubSpot connection
            result = hubspot_client.test_credentials({'api_key': api_key})
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error testing HubSpot: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/test-both', methods=['POST'])
    @login_required
    def test_both():
        """Test both ACGI and HubSpot credentials"""
        try:
            creds = get_app_credentials()
            username = creds.get('acgi_username')
            password = creds.get('acgi_password')
            environment = creds.get('acgi_environment', 'test')
            api_key = creds.get('hubspot_api_key')
            
            if not username or not password or not api_key:
                return jsonify({'success': False, 'message': 'All credentials must be configured'})
            
            # Test both connections
            acgi_result = acgi_client.test_credentials({
                'userid': username, 
                'password': password,
                'environment': environment
            })
            hubspot_result = hubspot_client.test_credentials({'api_key': api_key})
            
            if acgi_result['success'] and hubspot_result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Both ACGI and HubSpot connections successful',
                    'acgi': acgi_result,
                    'hubspot': hubspot_result
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'One or both connections failed',
                    'acgi': acgi_result,
                    'hubspot': hubspot_result
                })
        except Exception as e:
            logger.error(f"Error testing both connections: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/simulate-integration', methods=['POST'])
    def simulate_integration():
        """Simulate the integration process"""
        try:
            creds = get_app_credentials()
            acgi_credentials = {
                'userid': creds.get('acgi_username'),
                'password': creds.get('acgi_password'),
                'environment': creds.get('acgi_environment', 'test')
            }
            hubspot_credentials = {
                'api_key': creds.get('hubspot_api_key')
            }
            
            # Run integration
            result = integration_service.run_integration(acgi_credentials, hubspot_credentials)
            
            flash(f"Integration completed! {result['message']}", 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            logger.error(f"Error during integration: {str(e)}")
            flash(f"Integration failed: {str(e)}", 'error')
            return redirect(url_for('index'))

    @app.route('/start-scheduler', methods=['POST'])
    def start_scheduler():
        """Start the scheduled integration"""
        try:
            creds = get_app_credentials()
            acgi_credentials = {
                'userid': creds.get('acgi_username'),
                'password': creds.get('acgi_password'),
                'environment': creds.get('acgi_environment', 'test')
            }
            hubspot_credentials = {
                'api_key': creds.get('hubspot_api_key')
            }
            
            # Remove existing job if any
            try:
                scheduler.remove_job('acgi_hubspot_integration')
            except:
                pass
            
            # Add new scheduled job
            scheduler.add_job(
                func=lambda: integration_service.run_integration(acgi_credentials, hubspot_credentials),
                trigger='interval',
                minutes=10,
                id='acgi_hubspot_integration',
                name='ACGI to HubSpot Integration'
            )
            
            flash("Scheduler started! Integration will run every 10 minutes.", 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            flash(f"Failed to start scheduler: {str(e)}", 'error')
            return redirect(url_for('index'))

    @app.route('/stop-scheduler', methods=['POST'])
    def stop_scheduler():
        """Stop the scheduled integration"""
        try:
            scheduler.remove_job('acgi_hubspot_integration')
            flash("Scheduler stopped!", 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            flash(f"Failed to stop scheduler: {str(e)}", 'error')
            return redirect(url_for('index'))

    @app.route('/status')
    def status():
        """Get current scheduler status"""
        jobs = scheduler.get_jobs()
        return jsonify({
            'scheduler_running': scheduler.running,
            'jobs': [{'id': job.id, 'name': job.name, 'next_run': str(job.next_run_time)} for job in jobs]
        }) 