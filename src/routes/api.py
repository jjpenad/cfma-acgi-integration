from flask import request, jsonify, Blueprint
from utils import get_app_credentials, save_credentials, setup_logging
from models import get_session, FormField, SearchPreference
from services.hubspot_client import HubSpotClient
from routes.auth import login_required
from src.services.acgi_client import ACGIClient
from src.models import  ContactFieldMapping, AppState

logger = setup_logging()
hubspot_client = HubSpotClient()
api = Blueprint('api', __name__)

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
        print("object_type",object_type)
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
            print("creds",creds)
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

    @app.route('/api/acgi/customer/<customer_id>', methods=['GET'])
    def fetch_acgi_customer(customer_id):
        print("customer_id_get",customer_id)
        # Get global credentials from AppState
        creds = get_app_credentials()
        print("creds",creds)
        #check if acgi_credentials is set in the database
        if not creds:
            print("acgi_credentials not set")
            return jsonify({'error': 'ACGI credentials not set'}), 400
        credentials = {
            'userid': creds['acgi_username'],
            'password': creds['acgi_password'],
            'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
        }
        acgi_client = ACGIClient()
        result = acgi_client.get_customer_data(credentials, customer_id)
        print("result",result)
        if not result['success'] or not result['customers']:
            return jsonify({'error': 'Customer not found or fetch failed', 'details': result.get('message', '')}), 404
        # Flatten the customer data for mapping UI
        customer_data = result['customers'][0]
        return jsonify({'fields': customer_data})

    @app.route('/api/mapping/contact', methods=['GET', 'POST'])
    def contact_mapping():
        if request.method == 'POST':
            mapping = request.json.get('mapping', {})
            ContactFieldMapping.set_mapping(mapping)
            return jsonify({'status': 'success'})
        else:
            mapping = ContactFieldMapping.get_mapping()
            return jsonify({'mapping': mapping or {}})

    @app.route('/api/acgi-field-config', methods=['POST'])
    @login_required
    def save_acgi_field_config():
        data = request.get_json()
        object_type = data.get('object_type')
        config = data.get('config')
        if not object_type or config is None:
            return jsonify({'success': False, 'error': 'Missing object_type or config'}), 400
        session = get_session()
        try:
            key = f'acgi_field_config_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            if not obj:
                obj = AppState(key=key, value=json.dumps(config))
                session.add(obj)
            else:
                obj.value = json.dumps(config)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-field-config', methods=['GET'])
    @login_required
    def get_acgi_field_config():
        object_type = request.args.get('object_type')
        if not object_type:
            return jsonify({'success': False, 'error': 'Missing object_type'}), 400
        session = get_session()
        try:
            key = f'acgi_field_config_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            config = json.loads(obj.value) if obj and obj.value else {}
            return jsonify({'success': True, 'config': config})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-fields', methods=['POST'])
    @login_required
    def save_acgi_fields():
        data = request.get_json()
        object_type = data.get('object_type')
        fields = data.get('fields')
        if not object_type or fields is None:
            return jsonify({'success': False, 'error': 'Missing object_type or fields'}), 400
        session = get_session()
        try:
            key = f'acgi_fields_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            if not obj:
                obj = AppState(key=key, value=json.dumps(fields))
                session.add(obj)
            else:
                obj.value = json.dumps(fields)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-fields', methods=['GET'])
    @login_required
    def get_acgi_fields():
        object_type = request.args.get('object_type')
        if not object_type:
            return jsonify({'success': False, 'error': 'Missing object_type'}), 400
        session = get_session()
        try:
            key = f'acgi_fields_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            fields = json.loads(obj.value) if obj and obj.value else {}
            return jsonify({'success': True, 'fields': fields})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-address-preference', methods=['POST'])
    @login_required
    def save_acgi_address_preference():
        data = request.get_json()
        object_type = data.get('object_type')
        preference = data.get('preference')
        if not object_type or preference is None:
            return jsonify({'success': False, 'error': 'Missing object_type or preference'}), 400
        session = get_session()
        try:
            key = f'acgi_address_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            if not obj:
                obj = AppState(key=key, value=json.dumps(preference))
                session.add(obj)
            else:
                obj.value = json.dumps(preference)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-address-preference', methods=['GET'])
    @login_required
    def get_acgi_address_preference():
        object_type = request.args.get('object_type')
        if not object_type:
            return jsonify({'success': False, 'error': 'Missing object_type'}), 400
        session = get_session()
        try:
            key = f'acgi_address_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            preference = json.loads(obj.value) if obj and obj.value else {}
            return jsonify({'success': True, 'preference': preference})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-email-preference', methods=['POST'])
    @login_required
    def save_acgi_email_preference():
        data = request.get_json()
        object_type = data.get('object_type')
        preference = data.get('preference')
        if not object_type or preference is None:
            return jsonify({'success': False, 'error': 'Missing object_type or preference'}), 400
        session = get_session()
        try:
            key = f'acgi_email_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            if not obj:
                obj = AppState(key=key, value=json.dumps(preference))
                session.add(obj)
            else:
                obj.value = json.dumps(preference)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-email-preference', methods=['GET'])
    @login_required
    def get_acgi_email_preference():
        object_type = request.args.get('object_type')
        if not object_type:
            return jsonify({'success': False, 'error': 'Missing object_type'}), 400
        session = get_session()
        try:
            key = f'acgi_email_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            preference = json.loads(obj.value) if obj and obj.value else {}
            return jsonify({'success': True, 'preference': preference})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-phone-preference', methods=['POST'])
    @login_required
    def save_acgi_phone_preference():
        data = request.get_json()
        object_type = data.get('object_type')
        preference = data.get('preference')
        if not object_type or preference is None:
            return jsonify({'success': False, 'error': 'Missing object_type or preference'}), 400
        session = get_session()
        try:
            key = f'acgi_phone_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            if not obj:
                obj = AppState(key=key, value=json.dumps(preference))
                session.add(obj)
            else:
                obj.value = json.dumps(preference)
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/acgi-phone-preference', methods=['GET'])
    @login_required
    def get_acgi_phone_preference():
        object_type = request.args.get('object_type')
        if not object_type:
            return jsonify({'success': False, 'error': 'Missing object_type'}), 400
        session = get_session()
        try:
            key = f'acgi_phone_preference_{object_type}'
            from src.models import AppState
            obj = session.query(AppState).filter_by(key=key).first()
            import json
            preference = json.loads(obj.value) if obj and obj.value else {}
            return jsonify({'success': True, 'preference': preference})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close() 