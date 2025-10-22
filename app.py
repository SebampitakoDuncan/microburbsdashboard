from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import requests
import json
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def find_problematic_field(data):
    """
    Try to identify which field contains invalid JSON
    """
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    find_problematic_field(value)
                elif isinstance(value, list):
                    for item in value:
                        find_problematic_field(item)
                elif isinstance(value, str):
                    # Try to encode the string as JSON
                    try:
                        json.dumps(value)
                    except:
                        return f"String field '{key}': {repr(value[:100])}"
        elif isinstance(data, list):
            for item in data:
                result = find_problematic_field(item)
                if result:
                    return result
    except Exception as e:
        return f"Error analyzing data: {str(e)}"
    return None

def clean_nan_values(data):
    """
    Recursively clean NaN values from API response
    Convert NaN to None (null in JSON) which is JSON-compliant
    """
    try:
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Handle string representations of NaN, infinity, and empty values
                    if (value.lower() in ['nan', 'none', 'null', 'infinity', 'inf', '-inf', 'undefined'] or
                        value.strip() == '' or value == 'None' or value == 'NaN'):
                        logger.info(f"Converting invalid string to None: {value[:50]}")
                        cleaned[key] = None
                    else:
                        # Clean potentially problematic characters in strings
                        try:
                            # Remove or replace problematic Unicode characters
                            cleaned_value = value.replace('\u00a0', ' ').replace('\u00b2', ' sqm').replace('\u2013', '-').replace('\u2019', "'").replace('\u2022', '-')
                            # Ensure the string can be properly encoded in JSON
                            cleaned_value.encode('utf-8')
                            cleaned[key] = cleaned_value
                        except (UnicodeEncodeError, UnicodeDecodeError) as e:
                            logger.warning(f"Cleaning problematic characters in string field '{key}': {value[:50]}... Error: {str(e)}")
                            # Replace problematic characters with safe alternatives
                            cleaned_value = value.replace('\u00a0', ' ').replace('\u00b2', ' sqm').replace('\u2013', '-').replace('\u2019', "'").replace('\u2022', '-')
                            cleaned[key] = cleaned_value
                else:
                    cleaned[key] = clean_nan_values(value)
            return cleaned
        elif isinstance(data, list):
            return [clean_nan_values(item) for item in data]
        else:
            # Handle scalar values
            if isinstance(data, float):
                # Handle NaN and infinity values safely
                try:
                    if math.isnan(data) or math.isinf(data):
                        logger.info(f"Converting NaN/inf value to None: {data}")
                        return None
                    else:
                        return data
                except (ValueError, TypeError, OverflowError):
                    logger.info(f"Converting problematic float to None: {data}")
                    return None
            elif isinstance(data, str):
                # Handle string representations of NaN, infinity, and empty values
                if (data.lower() in ['nan', 'none', 'null', 'infinity', 'inf', '-inf', 'undefined'] or
                    data.strip() == '' or data == 'None' or data == 'NaN'):
                    logger.info(f"Converting invalid string to None: {data[:50]}")
                    return None
                else:
                    # Clean potentially problematic characters in strings
                    try:
                        # Remove or replace problematic Unicode characters
                        cleaned_value = data.replace('\u00a0', ' ').replace('\u00b2', ' sqm').replace('\u2013', '-').replace('\u2019', "'").replace('\u2022', '-')
                        # Ensure the string can be properly encoded in JSON
                        cleaned_value.encode('utf-8')
                        return cleaned_value
                    except (UnicodeEncodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Cleaning problematic characters in string: {data[:50]}... Error: {str(e)}")
                        # Replace problematic characters with safe alternatives
                        cleaned_value = data.replace('\u00a0', ' ').replace('\u00b2', ' sqm').replace('\u2013', '-').replace('\u2019', "'").replace('\u2022', '-')
                        return cleaned_value
            else:
                return data
    except Exception as e:
        logger.error(f"Error in clean_nan_values: {str(e)} with data: {str(data)[:200]}")
        # If cleaning fails, return None for safety
        return None

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
                data = response.json()
                logger.info(f"Successfully fetched {len(data.get('results', []))} properties")

                # Log the original data for debugging
                logger.info(f"Original data size: {len(str(data))} characters")

                # Clean up NaN values which are not valid JSON
                cleaned_data = clean_nan_values(data)
                logger.info(f"Cleaned data size: {len(str(cleaned_data))} characters")

                # Ensure the response is valid JSON
                try:
                    json_str = json.dumps(cleaned_data, ensure_ascii=False)
                    logger.info(f"JSON validation successful: {len(json_str)} characters")
                    return jsonify(cleaned_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON validation failed: {str(e)}")
                    logger.error(f"Cleaned data preview: {str(cleaned_data)[:500]}")

                    # Try to identify the problematic field
                    try:
                        problematic_field = find_problematic_field(cleaned_data)
                        logger.error(f"Problematic field: {problematic_field}")
                    except:
                        logger.error("Could not identify problematic field")

                    # Return error response with debugging info
                    return jsonify({
                        'error': f'Invalid JSON after cleaning: {str(e)}',
                        'data_size': len(str(cleaned_data)),
                        'data_preview': str(cleaned_data)[:1000] if str(cleaned_data) else 'No data',
                        'original_response_size': len(response.text)
                    }), 500
            except json.JSONDecodeError as e:
                logger.error(f"Original response is not valid JSON: {str(e)}")
                logger.error(f"Response status: {response.status_code}")
                logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                return jsonify({
                    'error': f'API returned invalid JSON: {str(e)}',
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'response_preview': response.text[:1000] if response.text else 'No response text'
                }), 500
            except Exception as e:
                logger.error(f"Error processing API response: {str(e)}")
                logger.error(f"Response status: {response.status_code}")
                logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                # Return error with details for debugging
                return jsonify({
                    'error': f'Error processing response: {str(e)}',
                    'response_length': len(response.text),
                    'status_code': response.status_code,
                    'response_preview': response.text[:1000] if response.text else 'No response text'
                }), 500
        else:
            logger.error(f"API request failed with status {response.status_code}")
            logger.error(f"API response: {response.text}")
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

@app.route('/test')
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({'test': 'success', 'message': 'Flask server is working'})

if __name__ == '__main__':
    print("Starting Property Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5001")
    print("API endpoint: http://localhost:5001/api/properties")
    app.run(debug=True, host='0.0.0.0', port=5001)
