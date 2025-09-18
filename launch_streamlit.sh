#!/bin/bash

# Launch just the Streamlit dashboard
echo "🚀 Starting Streamlit Dashboard..."
echo "📊 Available at: http://localhost:8501"

# Start the main Streamlit app
streamlit run streamlit_app/app.py --server.port 8501
