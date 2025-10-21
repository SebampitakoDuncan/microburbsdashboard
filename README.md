# Property Dashboard ✅ **LIVE & WORKING**

A comprehensive property market analysis dashboard that integrates with the Microburbs API to display real-time property data with interactive visualizations and insights.

**🌐 Live at:** http://localhost:5001
**📊 API:** Successfully fetching 8+ properties from Belmont North ✅ **JSON parsing fixed**
**🎨 UI:** **Material Design** with DM Sans font, professional blue color scheme
**📱 Mobile:** Fully responsive Material UI design

## Features

### 📊 **Data Analysis & Insights**
- **Jupyter Notebook Analysis**: Comprehensive data exploration using Pandas
- **Market Statistics**: Average price, median price, price ranges, land size analysis
- **Price per Square Meter**: Calculated metrics for property value assessment
- **Correlation Analysis**: Relationships between property features and pricing

### 🎯 **Interactive Dashboard**
- **Real-time Search**: Search by suburb and property type
- **Statistics Cards**: Key market metrics at a glance
- **Interactive Charts**: 
  - Price distribution histogram
  - Bedrooms vs average price analysis
  - Land size vs price scatter plot
  - Price per m² distribution
- **Sortable Property Table**: Click column headers to sort by any field
- **Property Details Modal**: Expandable property information with full descriptions

### 🎨 **User Experience**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Loading States**: Visual feedback during data fetching
- **Error Handling**: User-friendly error messages
- **Professional Styling**: Clean, modern interface

## Technology Stack

- **Backend**: Python Flask with CORS support
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Analysis**: Jupyter Notebook with Pandas, Matplotlib, Seaborn
- **Visualization**: Chart.js for interactive charts
- **API Integration**: Microburbs Property API

## Project Structure

```
/micro
├── analysis/
│   └── property_analysis.ipynb   # Jupyter notebook for data exploration
├── app.py                         # Flask application server
├── requirements.txt               # Python dependencies
├── static/
│   ├── index.html                 # Main dashboard HTML
│   ├── app.js                     # Vanilla JavaScript application
│   └── styles.css                 # Custom CSS styling
└── README.md                      # This file
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### 1. Clone and Navigate
```bash
cd /Users/duncan/Desktop/Cursor_Projects/micro
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

**✅ Dashboard is now live at:** **http://localhost:5001**

**What you'll see:**
- **Material Design** header with subtle texture overlay
- **DM Sans typography** for professional readability
- **Material UI color scheme** (blue primary, clean grays)
- **Quick suburb buttons** for easy demo testing
- **Interactive charts** with Chart.js (fixed canvas reuse)
- **Sortable property table** with Material styling
- **Professional search interface** with validation
- **Fully responsive** design optimized for all devices

### 5. Run Jupyter Analysis (Optional)
```bash
jupyter notebook analysis/property_analysis.ipynb
```

## Usage Guide

### Dashboard Features

#### 🔍 **Search Properties**
1. Enter a suburb name (e.g., "Belmont North")
2. Select property type (House, Unit, Townhouse)
3. Click "Search Properties" to fetch data

#### 📈 **Market Overview**
The dashboard displays key statistics:
- **Total Properties**: Number of current listings
- **Average Price**: Mean property price
- **Median Price**: Middle value of all prices
- **Price Range**: Minimum to maximum prices
- **Average Land Size**: Mean land area in square meters
- **Average Price/m²**: Price per square meter metric

#### 📊 **Interactive Charts**
- **Price Distribution**: Histogram showing price frequency
- **Bedrooms vs Price**: Bar chart of average price by bedroom count
- **Land Size vs Price**: Scatter plot showing correlation
- **Price per m²**: Distribution of price per square meter

#### 📋 **Property Table**
- Sortable columns: Address, Price, Beds, Baths, Land Size, Price/m², Listed Date
- Click any column header to sort ascending/descending
- "View Details" button opens property information modal
- Expandable property descriptions and full details

### Data Analysis Notebook

The Jupyter notebook (`analysis/property_analysis.ipynb`) provides:
- **Data Collection**: Automated API data fetching
- **Data Cleaning**: Processing and standardization
- **Statistical Analysis**: Comprehensive market metrics
- **Visualization**: Charts to inform dashboard design
- **Insights**: Key findings and recommendations

## API Integration

### Microburbs API
- **Endpoint**: `/api/properties`
- **Authentication**: Bearer token (test token included)
- **Parameters**: 
  - `suburb`: Suburb name (required)
  - `property_type`: Property type (optional, defaults to 'house')

### Example API Call
```python
import requests

url = "https://www.microburbs.com.au/report_generator/api/suburb/properties"
params = {
    "suburb": "Belmont North",
    "property_type": "house"
}
headers = {
    "Authorization": "Bearer test",
    "Content-Type": "application/json"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()
```

## Key Insights Discovered

Based on the analysis of Belmont North property data:

1. **Market Overview**: 8 properties currently listed
2. **Price Range**: $599,000 - $1,800,000
3. **Average Price**: $1,123,125
4. **Median Price**: $1,100,000
5. **Land Size Correlation**: Strong positive correlation between land size and price
6. **Property Types**: Mix of houses and units with varying bedroom counts
7. **Recent Listings**: Multiple properties listed in October 2025

## Development Notes

### Code Organization
- **Modular JavaScript**: Class-based architecture with clear separation of concerns
- **Responsive CSS**: Mobile-first design with CSS Grid and Flexbox
- **Error Handling**: Comprehensive error states and user feedback
- **Performance**: Optimized for fast loading and smooth interactions

### Future Enhancements
- Property comparison features
- Advanced filtering options
- Export functionality for data
- Historical price tracking
- Map integration for property locations

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 5001
   lsof -ti:5001 | xargs kill -9
   ```

2. **Module Not Found**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **JSON Parsing Errors**
   - ✅ Fixed: NaN values from API are automatically converted to null
   - ✅ Fixed: Chart.js canvas reuse errors resolved
   - ✅ Fixed: Search functionality works for all supported suburbs

4. **CORS Issues**
   - Flask-CORS is configured for development
   - For production, configure appropriate CORS policies

5. **API Rate Limits**
   - The test token has usage limits
   - For production, obtain proper API credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for demonstration purposes. Please respect the Microburbs API terms of service.

---

**Built with ❤️ using Python, Flask, and Vanilla JavaScript**
