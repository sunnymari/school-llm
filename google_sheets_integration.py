#!/usr/bin/env python3
"""
Google Sheets Integration for LLM Assessment
Allows teachers to input data directly in Google Sheets and sync with the assessment system.
"""

import streamlit as st
import pandas as pd
import requests
import json
from typing import Dict, List, Any
import io
import gspread
from google.oauth2.service_account import Credentials
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Google Sheets Integration",
    page_icon="📊",
    layout="wide"
)

# API base URL
API_BASE = "http://localhost:8000"

def setup_google_sheets():
    """Setup Google Sheets credentials and connection."""
    
    st.subheader("🔐 Google Sheets Setup")
    
    # Instructions
    st.markdown("""
    ### Setup Instructions:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable Google Sheets API
    4. Create a Service Account
    5. Download the JSON credentials file
    6. Share your Google Sheet with the service account email
    """)
    
    # File upload for credentials
    creds_file = st.file_uploader(
        "Upload Google Service Account JSON file",
        type=['json'],
        help="Download this from Google Cloud Console > Service Accounts"
    )
    
    if creds_file:
        try:
            # Save credentials temporarily
            creds_content = creds_file.read()
            with open("temp_creds.json", "wb") as f:
                f.write(creds_content)
            
            # Setup credentials
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file("temp_creds.json", scopes=scope)
            client = gspread.authorize(creds)
            
            st.success("✅ Google Sheets connected successfully!")
            
            # Clean up temp file
            os.remove("temp_creds.json")
            
            return client
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            return None
    
    return None

def create_assessment_sheet(client, sheet_name: str = "LLM Assessment Data"):
    """Create a new Google Sheet for assessment data."""
    try:
        # Create spreadsheet
        spreadsheet = client.create(sheet_name)
        
        # Create worksheets
        ws_responses = spreadsheet.add_worksheet(title="Student Responses", rows=100, cols=12)
        ws_schema = spreadsheet.add_worksheet(title="Assessment Schema", rows=20, cols=6)
        ws_mastery = spreadsheet.add_worksheet(title="Mastery Results", rows=100, cols=10)
        
        # Setup headers for responses sheet
        response_headers = ["Student", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"]
        ws_responses.update("A1:K1", [response_headers])
        
        # Setup headers for schema sheet
        schema_headers = ["Question", "PromptStub", "Topic", "Standard", "MaxPoints"]
        ws_schema.update("A1:E1", [schema_headers])
        
        # Add sample data to schema
        sample_schema = [
            [1, "What is the capital of France?", "Geography", "World Capitals", 2],
            [2, "Solve: 2x + 5 = 13", "Algebra", "Linear Equations", 3],
            [3, "Define photosynthesis", "Biology", "Plant Biology", 4],
            [4, "What caused World War I?", "History", "Modern History", 3],
            [5, "Calculate the area of a circle with radius 5", "Geometry", "Area and Perimeter", 3]
        ]
        ws_schema.update("A2:E6", sample_schema)
        
        # Setup headers for mastery sheet
        mastery_headers = ["Student", "Topic", "Mastery %", "Standard", "Mastery %", "Intervention Needed", "Last Updated"]
        ws_mastery.update("A1:G1", [mastery_headers])
        
        st.success(f"✅ Created Google Sheet: {sheet_name}")
        st.markdown(f"**Sheet URL:** {spreadsheet.url}")
        
        return spreadsheet
    
    except Exception as e:
        st.error(f"Failed to create sheet: {str(e)}")
        return None

def sync_from_sheets(client, spreadsheet_url: str):
    """Sync data from Google Sheets to the assessment system."""
    try:
        # Open spreadsheet
        spreadsheet = client.open_by_url(spreadsheet_url)
        
        # Get responses data
        ws_responses = spreadsheet.worksheet("Student Responses")
        responses_data = ws_responses.get_all_records()
        
        # Convert to DataFrame
        responses_df = pd.DataFrame(responses_data)
        
        # Validate data
        required_columns = ['Student', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10']
        if not all(col in responses_df.columns for col in required_columns):
            st.error(f"Sheet must contain columns: {required_columns}")
            return False
        
        # Save to CSV
        csv_content = responses_df.to_csv(index=False)
        
        # Upload to system (simulate by saving locally)
        with open("data/responses.csv", "w") as f:
            f.write(csv_content)
        
        # Get schema data
        try:
            ws_schema = spreadsheet.worksheet("Assessment Schema")
            schema_data = ws_schema.get_all_records()
            schema_df = pd.DataFrame(schema_data)
            
            # Save schema
            schema_csv = schema_df.to_csv(index=False)
            with open("data/assessment_schema.csv", "w") as f:
                f.write(schema_csv)
        except:
            st.warning("No Assessment Schema sheet found. Using default schema.")
        
        st.success("✅ Data synced from Google Sheets!")
        
        # Reload data in the system
        try:
            response = requests.post("http://localhost:8000/reload-data")
            if response.status_code == 200:
                st.success("✅ System data reloaded!")
            else:
                st.warning("⚠️ Data synced but system reload failed. Run the load script manually.")
        except:
            st.warning("⚠️ Data synced but could not reload system automatically.")
        
        return True
        
    except Exception as e:
        st.error(f"Failed to sync from sheets: {str(e)}")
        return False

def sync_to_sheets(client, spreadsheet_url: str):
    """Sync mastery results to Google Sheets."""
    try:
        # Get mastery data from API
        students_response = requests.get(f"{API_BASE}/students")
        if students_response.status_code != 200:
            st.error("Failed to get students from API")
            return False
        
        students = students_response.json()["students"]
        
        # Open spreadsheet
        spreadsheet = client.open_by_url(spreadsheet_url)
        ws_mastery = spreadsheet.worksheet("Mastery Results")
        
        # Clear existing data
        ws_mastery.clear()
        
        # Setup headers
        mastery_headers = ["Student", "Topic", "Mastery %", "Standard", "Mastery %", "Intervention Needed", "Last Updated"]
        ws_mastery.update("A1:G1", [mastery_headers])
        
        # Get mastery data for each student
        row = 2
        for student in students:
            mastery_response = requests.get(f"{API_BASE}/students/{student}/mastery")
            if mastery_response.status_code == 200:
                mastery_data = mastery_response.json()
                
                # Process topic mastery
                for topic in mastery_data.get('topic_mastery', []):
                    intervention_needed = "Yes" if topic['mastery_percentage'] < 70 else "No"
                    ws_mastery.update(f"A{row}:G{row}", [[
                        student,
                        topic['topic'],
                        f"{topic['mastery_percentage']:.1f}%",
                        "",  # Standard column
                        "",  # Standard mastery column
                        intervention_needed,
                        pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    ]])
                    row += 1
                
                # Process standard mastery
                for standard in mastery_data.get('standard_mastery', []):
                    intervention_needed = "Yes" if standard['mastery_percentage'] < 70 else "No"
                    ws_mastery.update(f"A{row}:G{row}", [[
                        student,
                        "",  # Topic column
                        "",  # Topic mastery column
                        standard['standard'],
                        f"{standard['mastery_percentage']:.1f}%",
                        intervention_needed,
                        pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    ]])
                    row += 1
        
        st.success("✅ Mastery results synced to Google Sheets!")
        return True
        
    except Exception as e:
        st.error(f"Failed to sync to sheets: {str(e)}")
        return False

def main():
    st.title("📊 Google Sheets Integration")
    st.markdown("Connect your assessment system with Google Sheets for easy data entry and sharing!")
    
    # Setup Google Sheets
    client = setup_google_sheets()
    
    if client:
        st.subheader("📋 Sheet Operations")
        
        tab1, tab2, tab3 = st.tabs(["🆕 Create New Sheet", "📥 Sync From Sheets", "📤 Sync To Sheets"])
        
        with tab1:
            st.markdown("Create a new Google Sheet with pre-configured templates for assessment data.")
            
            sheet_name = st.text_input("Sheet Name", value="LLM Assessment Data")
            
            if st.button("🆕 Create New Sheet", type="primary"):
                with st.spinner("Creating Google Sheet..."):
                    spreadsheet = create_assessment_sheet(client, sheet_name)
                    if spreadsheet:
                        st.markdown(f"**Share this sheet with your team:** {spreadsheet.url}")
        
        with tab2:
            st.markdown("Import data from your existing Google Sheet into the assessment system.")
            
            spreadsheet_url = st.text_input(
                "Google Sheet URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                help="Make sure the sheet has 'Student Responses' worksheet with proper headers"
            )
            
            if st.button("📥 Sync From Sheets", type="primary"):
                if spreadsheet_url:
                    with st.spinner("Syncing data from Google Sheets..."):
                        success = sync_from_sheets(client, spreadsheet_url)
                        if success:
                            st.success("✅ Data imported successfully! You can now use the assessment system.")
                else:
                    st.error("Please enter a valid Google Sheet URL")
        
        with tab3:
            st.markdown("Export mastery results and intervention recommendations to Google Sheets.")
            
            spreadsheet_url = st.text_input(
                "Google Sheet URL (for export)",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                help="Make sure the sheet has a 'Mastery Results' worksheet"
            )
            
            if st.button("📤 Sync To Sheets", type="primary"):
                if spreadsheet_url:
                    with st.spinner("Syncing mastery results to Google Sheets..."):
                        success = sync_to_sheets(client, spreadsheet_url)
                        if success:
                            st.success("✅ Mastery results exported successfully!")
                else:
                    st.error("Please enter a valid Google Sheet URL")
        
        # Template download
        st.subheader("📥 Download Templates")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Student Responses Template**")
            sample_responses = pd.DataFrame({
                'Student': ['Alice', 'Bob', 'Charlie'],
                'Q1': [2, 1, 2], 'Q2': [3, 2, 3], 'Q3': [3, 2, 4],
                'Q4': [2, 1, 3], 'Q5': [2, 1, 3], 'Q6': [3, 2, 4],
                'Q7': [2, 1, 2], 'Q8': [2, 1, 2], 'Q9': [2, 1, 2], 'Q10': [3, 2, 4]
            })
            
            csv_data = sample_responses.to_csv(index=False)
            st.download_button(
                label="📥 Download Responses Template",
                data=csv_data,
                file_name="student_responses_template.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("**Assessment Schema Template**")
            sample_schema = pd.DataFrame({
                'Question': [1, 2, 3, 4, 5],
                'PromptStub': ["What is...?", "Solve...", "Define...", "What caused...?", "Calculate..."],
                'Topic': ["Geography", "Algebra", "Biology", "History", "Geometry"],
                'Standard': ["World Capitals", "Linear Equations", "Plant Biology", "Modern History", "Area"],
                'MaxPoints': [2, 3, 4, 3, 3]
            })
            
            schema_csv = sample_schema.to_csv(index=False)
            st.download_button(
                label="📥 Download Schema Template",
                data=schema_csv,
                file_name="assessment_schema_template.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
