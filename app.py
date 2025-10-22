from flask import Flask, request, jsonify, send_from_directory, render_template_string, Response
from flask_cors import CORS
import requests
import json
import logging
import math
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def is_valid_json_string(s):
    """
    Check if a string can be safely included in JSON
    """
    try:
        json.dumps(s, ensure_ascii=False)
        return True
    except (TypeError, ValueError):
        return False

def sanitize_string_for_json(s):
    """
    Sanitize a string to make it safe for JSON inclusion
    """
    if not isinstance(s, str):
        return s

    # Remove null bytes and other problematic control characters
    s = s.replace('\x00', '').replace('\x01', '').replace('\x02', '')
    s = s.replace('\x03', '').replace('\x04', '').replace('\x05', '')
    s = s.replace('\x06', '').replace('\x07', '').replace('\x08', '')
    s = s.replace('\x0b', '').replace('\x0c', '').replace('\x0e', '')
    s = s.replace('\x0f', '').replace('\x10', '').replace('\x11', '')
    s = s.replace('\x12', '').replace('\x13', '').replace('\x14', '')
    s = s.replace('\x15', '').replace('\x16', '').replace('\x17', '')
    s = s.replace('\x18', '').replace('\x19', '').replace('\x1a', '')
    s = s.replace('\x1b', '').replace('\x1c', '').replace('\x1d', '')
    s = s.replace('\x1e', '').replace('\x1f', '')

    # Replace problematic Unicode characters
    s = s.replace('\u00a0', ' ')  # Non-breaking space
    s = s.replace('\u00b2', '²')  # Superscript 2
    s = s.replace('\u2013', '-')  # En dash
    s = s.replace('\u2019', "'")  # Right single quotation mark
    s = s.replace('\u2022', '•')  # Bullet

    # Use regex to find and replace any remaining control characters
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)

    return s

def validate_and_clean_json_data(data):
    """
    Recursively validate and clean data to ensure it's JSON-compatible
    Returns cleaned data or None if cleaning fails
    """
    try:
        if data is None:
            return None
        elif isinstance(data, (int, float)) and (math.isnan(data) if isinstance(data, float) else False):
            return None
        elif isinstance(data, str):
            # Handle NaN-like strings
            if data.lower().strip() in ['nan', 'none', 'null', 'infinity', 'inf', '-inf', 'undefined', '']:
                return None
            # Sanitize the string
            return sanitize_string_for_json(data)
        elif isinstance(data, dict):
            cleaned_dict = {}
            for key, value in data.items():
                if isinstance(key, str):
                    cleaned_key = sanitize_string_for_json(key)
                    cleaned_value = validate_and_clean_json_data(value)
                    if cleaned_key is not None:
                        cleaned_dict[cleaned_key] = cleaned_value
            return cleaned_dict
        elif isinstance(data, list):
            return [validate_and_clean_json_data(item) for item in data]
        else:
            return data
    except Exception as e:
        logger.warning(f"Error cleaning data: {str(e)}, returning None")
        return None

def safe_json_response(data):
    """
    Safely create a JSON response with proper error handling
    """
    try:
        # First validate and clean the data
        cleaned_data = validate_and_clean_json_data(data)

        # Try to serialize with ensure_ascii=False first (preserves Unicode)
        try:
            json_str = json.dumps(cleaned_data, ensure_ascii=False, separators=(',', ':'))
            return Response(json_str, mimetype='application/json')
        except (TypeError, ValueError, UnicodeEncodeError) as e:
            logger.warning(f"Unicode JSON failed, trying ASCII fallback: {str(e)}")
            # Fallback to ASCII encoding if Unicode fails
            json_str = json.dumps(cleaned_data, ensure_ascii=True, separators=(',', ':'))
            return Response(json_str, mimetype='application/json')

    except Exception as e:
        logger.error(f"Failed to create JSON response: {str(e)}")
        error_response = {
            'error': 'Data processing failed',
            'message': str(e),
            'data_type': type(data).__name__
        }
        return Response(json.dumps(error_response, ensure_ascii=True), mimetype='application/json', status=500)

# Legacy function kept for backward compatibility if needed
def clean_nan_values(data):
    """
    Legacy function - use validate_and_clean_json_data instead
    """
    return validate_and_clean_json_data(data)

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

        logger.info(f"Fetching properties for suburb: {suburb}, type: {property_type}")

        # Make request to Microburbs API
        response = requests.get(
            MICROBURBS_API_URL,
            params={'suburb': suburb, 'property_type': property_type},
            headers=API_HEADERS,
            timeout=30
        )

        logger.info(f"API response status: {response.status_code}")

        # Check if request was successful
        if response.status_code == 200:
            try:
                # Parse the JSON response with proper error handling
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse API response as JSON: {str(e)}")
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    logger.error(f"Response text preview: {response.text[:500]}")
                    return safe_json_response({
                        'error': 'API returned invalid JSON',
                        'message': str(e),
                        'status_code': response.status_code,
                        'response_preview': response.text[:200] if response.text else 'No response text'
                    })

                logger.info(f"Successfully fetched {len(data.get('results', []))} properties")
                logger.info(f"Original data size: {len(str(data))} characters")
                logger.info(f"Original data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                logger.info(f"Results count in original: {len(data.get('results', [])) if isinstance(data, dict) else 'N/A'}")

                # Use safe JSON response which handles all validation and cleaning
                cleaned_data = validate_and_clean_json_data(data)
                logger.info(f"Cleaned data keys: {list(cleaned_data.keys()) if isinstance(cleaned_data, dict) else 'Not a dict'}")
                logger.info(f"Results count in cleaned: {len(cleaned_data.get('results', [])) if isinstance(cleaned_data, dict) else 'N/A'}")

                return safe_json_response(cleaned_data)
            except Exception as e:
                logger.error(f"Unexpected error processing API response: {str(e)}")
                logger.error(f"Response status: {response.status_code}")
                return safe_json_response({
                    'error': 'Unexpected error processing response',
                    'message': str(e),
                    'status_code': response.status_code
                })
        else:
            logger.error(f"API request failed with status {response.status_code}")
            logger.error(f"API response: {response.text}")
            return safe_json_response({
                'error': f'API request failed with status {response.status_code}',
                'details': response.text[:500] if response.text else 'No response text'
            })

    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return safe_json_response({'error': 'Request timed out'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return safe_json_response({'error': f'Request failed: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return safe_json_response({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return safe_json_response({'status': 'healthy', 'service': 'property-dashboard'})

@app.route('/test')
def test_endpoint():
    """Simple test endpoint"""
    return safe_json_response({'test': 'success', 'message': 'Flask server is working'})

if __name__ == '__main__':
    print("Starting Property Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5001")
    print("API endpoint: http://localhost:5001/api/properties")
    app.run(debug=True, host='0.0.0.0', port=5001)
