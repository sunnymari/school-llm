import streamlit as st
import pandas as pd
import requests
import json
import io
from typing import Dict, List, Any

# Configure page
st.set_page_config(
    page_title="LLM Assessment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE = "http://localhost:8000"

def load_students():
    """Load list of students from API."""
    try:
        response = requests.get(f"{API_BASE}/students")
        if response.status_code == 200:
            return response.json()["students"]
        else:
            st.error("Failed to load students")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the server is running on localhost:8000")
        return []

def get_student_mastery(student_name: str) -> Dict[str, Any]:
    """Get mastery data for a student."""
    try:
        response = requests.get(f"{API_BASE}/students/{student_name}/mastery")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to load mastery data for {student_name}")
            return {}
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API")
        return {}

def ask_question(student_name: str, question: str, threshold: float = 70.0) -> Dict[str, Any]:
    """Ask a question about a student."""
    try:
        payload = {
            "student_name": student_name,
            "question": question,
            "threshold": threshold
        }
        response = requests.post(f"{API_BASE}/ask", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get AI response: {response.text}")
            return {}
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API")
        return {}

def process_csv_upload(uploaded_file) -> str:
    """Process uploaded CSV and return mastery data."""
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Display preview
        st.subheader("📄 CSV Preview")
        st.dataframe(df.head())
        
        # Validate CSV format
        required_columns = ['Student', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10']
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV must contain columns: {required_columns}")
            return ""
        
        # Process each student
        results = []
        for _, row in df.iterrows():
            student_name = row['Student']
            
            # Get mastery data
            mastery_data = get_student_mastery(student_name)
            if mastery_data:
                # Create summary
                topic_summary = {}
                for topic in mastery_data.get('topic_mastery', []):
                    topic_summary[topic['topic']] = f"{topic['mastery_percentage']:.1f}%"
                
                standard_summary = {}
                for standard in mastery_data.get('standard_mastery', []):
                    standard_summary[standard['standard']] = f"{standard['mastery_percentage']:.1f}%"
                
                results.append({
                    'Student': student_name,
                    'Topic_Mastery': json.dumps(topic_summary),
                    'Standard_Mastery': json.dumps(standard_summary),
                    'Overall_Average': sum([topic['mastery_percentage'] for topic in mastery_data.get('topic_mastery', [])]) / max(len(mastery_data.get('topic_mastery', [])), 1)
                })
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Convert to CSV string
        output = io.StringIO()
        results_df.to_csv(output, index=False)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        return ""

def main():
    st.title("🎓 LLM Assessment Dashboard")
    st.markdown("Upload CSV files, analyze student mastery, and get AI-powered insights!")
    
    # Sidebar for navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📊 Student Analysis", 
        "📁 CSV Upload & Download", 
        "🤖 AI Q&A Assistant"
    ])
    
    if page == "📊 Student Analysis":
        show_student_analysis()
    elif page == "📁 CSV Upload & Download":
        show_csv_upload()
    elif page == "🤖 AI Q&A Assistant":
        show_ai_assistant()

def show_student_analysis():
    st.header("📊 Student Performance Analysis")
    
    # Load students
    students = load_students()
    
    if not students:
        st.warning("No students found. Make sure to load data first using the scripts.")
        return
    
    # Student selector
    selected_student = st.selectbox("Select a student", students)
    
    if selected_student:
        # Get mastery data
        mastery_data = get_student_mastery(selected_student)
        
        if mastery_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📚 Topic Mastery")
                topic_data = []
                for topic in mastery_data.get('topic_mastery', []):
                    topic_data.append({
                        'Topic': topic['topic'],
                        'Score': f"{topic['total_points']}/{topic['max_points']}",
                        'Percentage': f"{topic['mastery_percentage']:.1f}%"
                    })
                
                if topic_data:
                    topic_df = pd.DataFrame(topic_data)
                    st.dataframe(topic_df, use_container_width=True)
                    
                    # Create chart
                    chart_data = pd.DataFrame({
                        'Topic': [t['topic'] for t in mastery_data.get('topic_mastery', [])],
                        'Mastery %': [t['mastery_percentage'] for t in mastery_data.get('topic_mastery', [])]
                    })
                    st.bar_chart(chart_data.set_index('Topic'))
            
            with col2:
                st.subheader("🎯 Standard Mastery")
                standard_data = []
                for standard in mastery_data.get('standard_mastery', []):
                    standard_data.append({
                        'Standard': standard['standard'],
                        'Score': f"{standard['total_points']}/{standard['max_points']}",
                        'Percentage': f"{standard['mastery_percentage']:.1f}%"
                    })
                
                if standard_data:
                    standard_df = pd.DataFrame(standard_data)
                    st.dataframe(standard_df, use_container_width=True)

def show_csv_upload():
    st.header("📁 CSV Upload & Mastery Download")
    
    st.markdown("""
    ### How to use:
    1. Upload a CSV file with student responses (format: Student, Q1, Q2, ..., Q10)
    2. The system will analyze each student's mastery
    3. Download the results as a CSV file
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="CSV should have columns: Student, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10"
    )
    
    if uploaded_file is not None:
        # Process button
        if st.button("🔄 Process CSV", type="primary"):
            with st.spinner("Processing CSV and analyzing mastery..."):
                results_csv = process_csv_upload(uploaded_file)
                
                if results_csv:
                    st.success("✅ Processing complete!")
                    
                    # Display results
                    st.subheader("📊 Results Preview")
                    results_df = pd.read_csv(io.StringIO(results_csv))
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Mastery Results",
                        data=results_csv,
                        file_name="student_mastery_results.csv",
                        mime="text/csv"
                    )
    
    # Sample CSV format
    st.subheader("📋 Sample CSV Format")
    sample_data = {
        'Student': ['Alice', 'Bob', 'Charlie'],
        'Q1': [2, 1, 2], 'Q2': [3, 2, 3], 'Q3': [3, 2, 4],
        'Q4': [2, 1, 3], 'Q5': [2, 1, 3], 'Q6': [3, 2, 4],
        'Q7': [2, 1, 2], 'Q8': [2, 1, 2], 'Q9': [2, 1, 2], 'Q10': [3, 2, 4]
    }
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df, use_container_width=True)
    
    # Download sample
    sample_csv = sample_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_responses.csv",
        mime="text/csv"
    )

def show_ai_assistant():
    st.header("🤖 AI Q&A Assistant")
    
    st.markdown("""
    Ask questions about student performance and get AI-powered insights with intervention strategies!
    """)
    
    # Load students
    students = load_students()
    
    if not students:
        st.warning("No students found. Make sure to load data first.")
        return
    
    # Input form
    with st.form("ai_question_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_student = st.selectbox("Select a student", students)
            threshold = st.slider("Mastery threshold (%)", 0, 100, 70)
        
        with col2:
            question = st.text_area(
                "Ask a question",
                placeholder="e.g., What areas should this student focus on improving?",
                height=100
            )
        
        submitted = st.form_submit_button("🤖 Ask AI", type="primary")
    
    if submitted and question:
        with st.spinner("Getting AI response..."):
            response = ask_question(selected_student, question, threshold)
            
            if response:
                st.success("✅ AI Response Generated!")
                
                # Display response
                st.subheader("💬 AI Answer")
                st.markdown(response.get('answer', 'No answer provided'))
                
                # Display mastery summary
                st.subheader("📊 Student Mastery Summary")
                mastery_summary = response.get('mastery_summary', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Topic Mastery:**")
                    for topic in mastery_summary.get('topic_mastery', []):
                        st.markdown(f"- {topic['topic']}: {topic['mastery_percentage']:.1f}%")
                
                with col2:
                    st.markdown("**Standard Mastery:**")
                    for standard in mastery_summary.get('standard_mastery', []):
                        st.markdown(f"- {standard['standard']}: {standard['mastery_percentage']:.1f}%")
                
                # Display intervention plan
                st.subheader("🎯 Intervention Plan")
                intervention_plan = response.get('intervention_plan', '')
                st.markdown(intervention_plan)
    
    # Example questions
    st.subheader("💡 Example Questions")
    example_questions = [
        "What areas should this student focus on improving?",
        "What intervention strategies would work best for this student?",
        "How is this student performing compared to expectations?",
        "What are this student's strengths and weaknesses?",
        "What specific teaching strategies should I use?"
    ]
    
    for i, example in enumerate(example_questions):
        if st.button(f"📝 {example}", key=f"example_{i}"):
            st.session_state.example_question = example

if __name__ == "__main__":
    main()
