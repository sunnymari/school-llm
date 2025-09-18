#!/bin/bash

# Launch LTI Canvas integration
echo "🚀 Starting LTI Canvas Integration..."
echo "🎓 Available at: http://localhost:8503"

# Start the LTI Streamlit app
streamlit run lti_integration/lti_app.py --server.port 8503
