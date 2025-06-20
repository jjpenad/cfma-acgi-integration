from flask import request, jsonify
from utils import get_app_credentials, save_credentials, setup_logging
from models import get_session, FormField, SearchPreference
from services.hubspot_client import HubSpotClient
from routes.auth import login_required

logger = setup_logging()
hubspot_client = HubSpotClient()

def init_api_routes(app):
    """Initialize API routes"""
    
    @app.route('/api/credentials', methods=['GET'])
    @login_required
    def get_credentials():
        """Get saved credentials"""
        try:
            creds = get_app_credentials()
            return jsonify({
                'success': True,
                'credentials': {
                    'acgi_username': creds.get('acgi_username', ''),
                    'acgi_password': creds.get('acgi_password', ''),
                    'acgi_environment': creds.get('acgi_environment', 'test'),
                    'hubspot_api_key': creds.get('hubspot_api_key', '')
                }
            })
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/hubspot-properties/<object_type>', methods=['GET'])
    @login_required
    def get_hubspot_properties_by_type(object_type):
        """Get available HubSpot properties for specific object type"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Get properties based on object type
            if object_type == 'contacts':
                properties = hubspot_client.get_contact_properties()
            elif object_type == 'deals':
                properties = hubspot_client.get_deal_properties()
            else:
                return jsonify({'error': f'Unsupported object type: {object_type}'}), 400
            
            # Get important fields from database
            session = get_session()
            try:
                db_fields = session.query(FormField).filter_by(object_type=object_type).all()
                db_field_names = {field.field_name: field for field in db_fields}
            finally:
                session.close()
            
            # Categorize properties
            important_properties = []
            other_properties = []
            
            for prop in properties:
                field_name = prop.get('name', '')
                is_important = db_field_names.get(field_name, FormField()).is_important == 'true'
                is_enabled = db_field_names.get(field_name, FormField()).is_enabled == 'true'
                
                prop['is_enabled'] = is_enabled
                
                if is_important:
                    important_properties.append(prop)
                else:
                    other_properties.append(prop)
            
            # Sort important properties by order
            important_properties.sort(key=lambda x: db_field_names.get(x.get('name', ''), FormField()).order_index or 0)
            
            # Sort other properties alphabetically by name
            other_properties.sort(key=lambda x: x.get('name', ''))
            
            return jsonify({
                'important_properties': important_properties,  # Show all important properties
                'other_properties': other_properties
            })
        
        except Exception as e:
            logger.error(f"Error getting HubSpot properties: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/save-form-field', methods=['POST'])
    @login_required
    def save_form_field():
        """Save form field configuration to database"""
        try:
            data = request.get_json()
            object_type = data.get('object_type')
            field_name = data.get('field_name')
            field_label = data.get('field_label', '')
            field_type = data.get('field_type', 'text')
            is_enabled = data.get('is_enabled')
            is_important = data.get('is_important')
            order_index = data.get('order_index', 0)
            
            session = get_session()
            try:
                # Check if field exists
                existing_field = session.query(FormField).filter_by(
                    object_type=object_type, 
                    field_name=field_name
                ).first()
                
                if existing_field:
                    # Update existing field - only update provided fields
                    if field_label is not None:
                        existing_field.field_label = field_label
                    if field_type is not None:
                        existing_field.field_type = field_type
                    if is_enabled is not None:
                        existing_field.is_enabled = str(is_enabled).lower()
                    if is_important is not None:
                        existing_field.is_important = str(is_important).lower()
                    if order_index is not None:
                        existing_field.order_index = order_index
                else:
                    # Create new field
                    new_field = FormField(
                        object_type=object_type,
                        field_name=field_name,
                        field_label=field_label,
                        field_type=field_type,
                        is_enabled=str(is_enabled).lower() if is_enabled is not None else 'false',
                        is_important=str(is_important).lower() if is_important is not None else 'false',
                        order_index=order_index
                    )
                    session.add(new_field)
                
                session.commit()
                
                return jsonify({'success': True, 'message': 'Field configuration saved'})
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Error saving form field: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/save-to-hubspot/<object_type>', methods=['POST'])
    @login_required
    def save_to_hubspot(object_type):
        """Save data to HubSpot for specific object type"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            data = request.get_json()
            object_data = data.get('object_data', {})
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Get search preference for contacts
            search_strategy = 'email_only'  # default
            if object_type == 'contacts':
                session = get_session()
                try:
                    preference = session.query(SearchPreference).filter_by(
                        object_type=object_type
                    ).first()
                    if preference:
                        search_strategy = preference.search_strategy
                finally:
                    session.close()
            
            # Save based on object type
            if object_type == 'contacts':
                result = hubspot_client.create_or_update_contact(object_data, search_strategy)
            elif object_type == 'deals':
                result = hubspot_client.create_deal(object_data)
            else:
                return jsonify({'error': f'Unsupported object type: {object_type}'}), 400
            
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error saving to HubSpot: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hubspot-properties', methods=['GET'])
    @login_required
    def get_hubspot_properties():
        """Get available HubSpot contact properties"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Get contact properties
            properties = hubspot_client.get_contact_properties()
            return jsonify({'properties': properties})
        
        except Exception as e:
            logger.error(f"Error getting HubSpot properties: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hubspot-contacts', methods=['GET'])
    @login_required
    def get_hubspot_contacts():
        """Get HubSpot contacts for deal association"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Get contacts
            contacts = hubspot_client.get_contacts(limit=100)
            return jsonify({'contacts': contacts})
        
        except Exception as e:
            logger.error(f"Error getting HubSpot contacts: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/create-contact', methods=['POST'])
    @login_required
    def create_contact():
        """Create a new contact in HubSpot"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            data = request.get_json()
            contact_data = data.get('contact_data', {})
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Create contact
            result = hubspot_client.create_or_update_contact(contact_data)
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/create-deal', methods=['POST'])
    @login_required
    def create_deal():
        """Create a new deal in HubSpot"""
        try:
            creds = get_app_credentials()
            api_key = creds.get('hubspot_api_key')
            if not api_key:
                return jsonify({'error': 'API key required. Please set it on the home page.'}), 400
            
            data = request.get_json()
            deal_data = data.get('deal_data', {})
            
            # Initialize HubSpot client
            if not hubspot_client.initialize_client(api_key):
                return jsonify({'error': 'Failed to initialize HubSpot client'}), 500
            
            # Create deal
            result = hubspot_client.create_deal(deal_data)
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error creating deal: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/save-search-preference', methods=['POST'])
    @login_required
    def save_search_preference():
        """Save search preference for an object type"""
        try:
            data = request.get_json()
            object_type = data.get('object_type')
            search_strategy = data.get('search_strategy')
            
            if not object_type or not search_strategy:
                return jsonify({'error': 'Object type and search strategy are required'}), 400
            
            session = get_session()
            try:
                # Check if preference exists
                existing_preference = session.query(SearchPreference).filter_by(
                    object_type=object_type
                ).first()
                
                if existing_preference:
                    # Update existing preference
                    existing_preference.search_strategy = search_strategy
                else:
                    # Create new preference
                    new_preference = SearchPreference(
                        object_type=object_type,
                        search_strategy=search_strategy
                    )
                    session.add(new_preference)
                
                session.commit()
                
                return jsonify({'success': True, 'message': 'Search preference saved'})
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Error saving search preference: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/get-search-preference/<object_type>', methods=['GET'])
    @login_required
    def get_search_preference(object_type):
        """Get search preference for an object type"""
        try:
            session = get_session()
            try:
                preference = session.query(SearchPreference).filter_by(
                    object_type=object_type
                ).first()
                
                if preference:
                    return jsonify({
                        'success': True,
                        'search_strategy': preference.search_strategy
                    })
                else:
                    # Return default preference
                    return jsonify({
                        'success': True,
                        'search_strategy': 'email_only'
                    })
            
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Error getting search preference: {str(e)}")
            return jsonify({'error': str(e)}), 500 