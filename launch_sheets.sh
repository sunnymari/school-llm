#!/bin/bash

# Launch Google Sheets integration
echo "🚀 Starting Google Sheets Integration..."
echo "📋 Available at: http://localhost:8502"

# Start the Google Sheets Streamlit app
streamlit run web_ui/google_sheets_integration.py --server.port 8502
