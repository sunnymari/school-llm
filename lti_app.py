#!/usr/bin/env python3
"""
LTI (Learning Tools Interoperability) Integration for Canvas/Google Classroom
Provides a sidebar interface that can be embedded in learning management systems.
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Any, Optional
import urllib.parse
import hashlib
import hmac
import time
import os

# Configure Streamlit for LTI
st.set_page_config(
    page_title="LLM Assessment LTI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE = "http://localhost:8000"

class LTITool:
    """LTI Tool implementation for Canvas/Google Classroom integration."""
    
    def __init__(self):
        self.consumer_key = os.getenv("LTI_CONSUMER_KEY", "llm_assessment_key")
        self.consumer_secret = os.getenv("LTI_CONSUMER_SECRET", "llm_assessment_secret")
    
    def validate_lti_request(self, request_data: Dict[str, str]) -> bool:
        """Validate LTI request signature."""
        try:
            # Extract signature from request
            signature = request_data.get('oauth_signature', '')
            received_signature = request_data.get('oauth_signature', '')
            
            # Create signature base string
            base_string = self._create_signature_base_string(request_data)
            
            # Calculate expected signature
            expected_signature = self._calculate_signature(base_string, self.consumer_secret)
            
            return hmac.compare_digest(received_signature, expected_signature)
        except Exception as e:
            st.error(f"LTI validation error: {str(e)}")
            return False
    
    def _create_signature_base_string(self, params: Dict[str, str]) -> str:
        """Create signature base string for OAuth."""
        # Remove oauth_signature from params
        filtered_params = {k: v for k, v in params.items() if k != 'oauth_signature'}
        
        # Sort parameters
        sorted_params = sorted(filtered_params.items())
        
        # Create query string
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        return f"POST&{urllib.parse.quote('http://localhost:8501', safe='')}&{urllib.parse.quote(query_string)}"
    
    def _calculate_signature(self, base_string: str, secret: str) -> str:
        """Calculate HMAC-SHA1 signature."""
        return hmac.new(
            secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()

def get_student_from_context(user_info: Dict[str, str]) -> str:
    """Extract student identifier from LTI context."""
    # Try different possible fields for student identification
    student_id = (
        user_info.get('user_id') or
        user_info.get('lis_person_sourcedid') or
        user_info.get('custom_canvas_user_id') or
        user_info.get('custom_canvas_user_login_id') or
        user_info.get('ext_user_username') or
        "Unknown Student"
    )
    return student_id

def load_lti_context():
    """Load LTI context from query parameters or session state."""
    # Check if we have LTI parameters in query string
    try:
        query_params = st.query_params
    except AttributeError:
        # Fallback for older Streamlit versions
        query_params = {}
    
    lti_context = {}
    
    # Extract common LTI parameters
    lti_fields = [
        'user_id', 'lis_person_name_given', 'lis_person_name_family',
        'lis_person_contact_email_primary', 'context_id', 'context_title',
        'context_label', 'resource_link_id', 'resource_link_title',
        'custom_canvas_user_id', 'custom_canvas_user_login_id',
        'ext_user_username', 'roles', 'launch_presentation_return_url'
    ]
    
    for field in lti_fields:
        if field in query_params:
            lti_context[field] = query_params[field]
    
    # Store in session state
    if lti_context:
        st.session_state.lti_context = lti_context
    
    return st.session_state.get('lti_context', {})

def get_student_mastery_from_api(student_name: str) -> Dict[str, Any]:
    """Get mastery data from API."""
    try:
        response = requests.get(f"{API_BASE}/students/{student_name}/mastery")
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except:
        return {}

def ask_ai_question(student_name: str, question: str, threshold: float = 70.0) -> Dict[str, Any]:
    """Ask AI question via API."""
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
            return {}
    except:
        return {}

def show_lti_sidebar():
    """Display the LTI sidebar interface."""
    
    # Load LTI context
    lti_context = load_lti_context()
    
    if not lti_context:
        st.warning("⚠️ No LTI context found. This tool should be launched from Canvas or Google Classroom.")
        st.markdown("""
        ### For Canvas Integration:
        1. Go to your Canvas course
        2. Add External Tool
        3. Use URL: `http://your-server:8501`
        4. Configure LTI credentials
        """)
        return
    
    # Display user info
    st.sidebar.title("🎓 Assessment Dashboard")
    
    user_name = f"{lti_context.get('lis_person_name_given', '')} {lti_context.get('lis_person_name_family', '')}".strip()
    if user_name:
        st.sidebar.markdown(f"**Student:** {user_name}")
    
    course_title = lti_context.get('context_title', 'Unknown Course')
    st.sidebar.markdown(f"**Course:** {course_title}")
    
    # Get student identifier
    student_id = get_student_from_context(lti_context)
    st.sidebar.markdown(f"**Student ID:** {student_id}")
    
    # Check if student exists in system
    try:
        students_response = requests.get(f"{API_BASE}/students")
        available_students = students_response.json().get("students", []) if students_response.status_code == 200 else []
    except:
        available_students = []
    
    # If student not found, show message
    if student_id not in available_students and available_students:
        st.sidebar.warning("Student not found in assessment system")
        st.sidebar.markdown("**Available students:**")
        for student in available_students[:5]:  # Show first 5
            st.sidebar.markdown(f"- {student}")
        return
    
    # Main content area
    st.title("🎓 Student Assessment Dashboard")
    
    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs(["📊 Performance", "🤖 AI Assistant", "📈 Progress"])
    
    with tab1:
        show_performance_tab(student_id)
    
    with tab2:
        show_ai_assistant_tab(student_id)
    
    with tab3:
        show_progress_tab(student_id)

def show_performance_tab(student_id: str):
    """Show student performance tab."""
    st.header("📊 Performance Overview")
    
    # Get mastery data
    mastery_data = get_student_mastery_from_api(student_id)
    
    if not mastery_data:
        st.error("No performance data available for this student.")
        return
    
    # Display topic mastery
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Topic Mastery")
        topic_data = mastery_data.get('topic_mastery', [])
        
        if topic_data:
            for topic in topic_data:
                mastery_pct = topic['mastery_percentage']
                color = "green" if mastery_pct >= 80 else "orange" if mastery_pct >= 70 else "red"
                
                st.markdown(f"""
                **{topic['topic']}**
                - Score: {topic['total_points']}/{topic['max_points']}
                - Mastery: <span style="color: {color}">{mastery_pct:.1f}%</span>
                """, unsafe_allow_html=True)
        else:
            st.info("No topic mastery data available")
    
    with col2:
        st.subheader("🎯 Standard Mastery")
        standard_data = mastery_data.get('standard_mastery', [])
        
        if standard_data:
            for standard in standard_data:
                mastery_pct = standard['mastery_percentage']
                color = "green" if mastery_pct >= 80 else "orange" if mastery_pct >= 70 else "red"
                
                st.markdown(f"""
                **{standard['standard']}**
                - Score: {standard['total_points']}/{standard['max_points']}
                - Mastery: <span style="color: {color}">{mastery_pct:.1f}%</span>
                """, unsafe_allow_html=True)
        else:
            st.info("No standard mastery data available")
    
    # Performance summary
    if topic_data:
        avg_mastery = sum(t['mastery_percentage'] for t in topic_data) / len(topic_data)
        st.metric("Overall Mastery", f"{avg_mastery:.1f}%")

def show_ai_assistant_tab(student_id: str):
    """Show AI assistant tab."""
    st.header("🤖 AI Learning Assistant")
    
    # Quick question buttons
    st.subheader("💡 Quick Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 How am I doing?", key="q1"):
            st.session_state.quick_question = "How am I performing overall in this course?"
        
        if st.button("🎯 What should I focus on?", key="q2"):
            st.session_state.quick_question = "What areas should I focus on improving?"
    
    with col2:
        if st.button("📚 Study strategies?", key="q3"):
            st.session_state.quick_question = "What study strategies would work best for me?"
        
        if st.button("❓ Any concerns?", key="q4"):
            st.session_state.quick_question = "Are there any areas of concern in my performance?"
    
    # Custom question input
    st.subheader("💬 Ask a Custom Question")
    
    # Pre-fill with quick question if selected
    default_question = st.session_state.get('quick_question', '')
    
    question = st.text_area(
        "Ask me anything about your performance:",
        value=default_question,
        placeholder="e.g., What topics should I review before the next exam?",
        height=100
    )
    
    if st.button("🤖 Get AI Response", type="primary"):
        if question:
            with st.spinner("Getting AI response..."):
                response = ask_ai_question(student_id, question, 70.0)
                
                if response and response.get('answer'):
                    st.success("✅ AI Response Generated!")
                    
                    # Display AI answer
                    st.markdown("**🤖 AI Response:**")
                    st.markdown(response['answer'])
                    
                    # Display intervention plan if available
                    intervention_plan = response.get('intervention_plan', '')
                    if intervention_plan and intervention_plan != "Great job! This student is performing well across all areas and doesn't need specific interventions at this time.":
                        st.markdown("**🎯 Recommended Actions:**")
                        st.markdown(intervention_plan)
                else:
                    st.error("Failed to get AI response. Please try again.")
        else:
            st.warning("Please enter a question first.")
    
    # Clear quick question after use
    if 'quick_question' in st.session_state:
        del st.session_state.quick_question

def show_progress_tab(student_id: str):
    """Show progress tracking tab."""
    st.header("📈 Progress Tracking")
    
    # Get mastery data
    mastery_data = get_student_mastery_from_api(student_id)
    
    if not mastery_data:
        st.info("No progress data available yet.")
        return
    
    # Create progress indicators
    topic_data = mastery_data.get('topic_mastery', [])
    
    if topic_data:
        st.subheader("📚 Topic Progress")
        
        for topic in topic_data:
            mastery_pct = topic['mastery_percentage']
            
            # Progress bar
            progress_color = "green" if mastery_pct >= 80 else "orange" if mastery_pct >= 70 else "red"
            
            st.markdown(f"**{topic['topic']}**")
            st.progress(mastery_pct / 100)
            st.markdown(f"Current: {mastery_pct:.1f}% | Target: 80%")
            st.markdown("---")
        
        # Overall progress
        avg_mastery = sum(t['mastery_percentage'] for t in topic_data) / len(topic_data)
        st.subheader("🎯 Overall Progress")
        st.progress(avg_mastery / 100)
        st.metric("Average Mastery", f"{avg_mastery:.1f}%")
        
        # Recommendations
        if avg_mastery < 70:
            st.warning("⚠️ Consider focusing on areas with lower mastery scores.")
        elif avg_mastery < 80:
            st.info("💡 Good progress! Continue practicing to reach mastery.")
        else:
            st.success("🎉 Excellent! You've achieved mastery in most areas.")

def main():
    """Main LTI application."""
    
    # Initialize LTI tool
    lti_tool = LTITool()
    
    # Show sidebar interface
    show_lti_sidebar()

if __name__ == "__main__":
    main()
