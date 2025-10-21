from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def clean_nan_values(data):
    """
    Recursively clean NaN values from API response
    Convert NaN to None (null in JSON) which is JSON-compliant
    """
    import math

    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, float) and math.isnan(value):
                # Convert NaN to None (null in JSON)
                cleaned[key] = None
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_nan_values(value)
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    else:
        # Handle scalar NaN values
        if isinstance(data, float) and math.isnan(data):
            return None
        return data

# Microburbs API configuration
MICROBURBS_API_URL = "https://www.microburbs.com.au/report_generator/api/suburb/properties"
API_HEADERS = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/properties')
def get_properties():
    """
    Proxy endpoint for Microburbs API
    Query parameters:
    - suburb: Suburb name (required)
    - property_type: Type of property (optional, defaults to 'house')
    """
    try:
        # Get query parameters
        suburb = request.args.get('suburb')
        property_type = request.args.get('property_type', 'house')
        
        if not suburb:
            return jsonify({'error': 'suburb parameter is required'}), 400
        
        # Prepare API request
        params = {
            'suburb': suburb,
            'property_type': property_type
        }
        
        logger.info(f"Fetching properties for suburb: {suburb}, type: {property_type}")
        
        # Make request to Microburbs API
        response = requests.get(
            MICROBURBS_API_URL,
            params=params,
            headers=API_HEADERS,
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully fetched {len(data.get('results', []))} properties")

            # Clean up NaN values which are not valid JSON
            cleaned_data = clean_nan_values(data)
            return jsonify(cleaned_data)
        else:
            logger.error(f"API request failed with status {response.status_code}")
            return jsonify({
                'error': f'API request failed with status {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return jsonify({'error': 'Request timed out'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': f'Request failed: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'property-dashboard'})

if __name__ == '__main__':
    print("Starting Property Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5001")
    print("API endpoint: http://localhost:5001/api/properties")
    app.run(debug=True, host='0.0.0.0', port=5001)
