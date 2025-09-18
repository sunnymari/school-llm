#!/usr/bin/env python3
"""
Simple Assessment Dashboard - No complex imports
"""

import streamlit as st
import pandas as pd
import requests
import json

# Configure page
st.set_page_config(
    page_title="Math Assessment Dashboard",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🧮 Math Assessment Dashboard")
    st.markdown("View your counting assessment results and get AI insights!")
    
    # Sidebar for navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📊 Student Overview", 
        "🤖 AI Insights",
        "📈 Performance Analysis"
    ])
    
    if page == "📊 Student Overview":
        show_student_overview()
    elif page == "🤖 AI Insights":
        show_ai_insights()
    elif page == "📈 Performance Analysis":
        show_performance_analysis()

def show_student_overview():
    st.header("📊 Student Overview")
    
    # Get students from API
    try:
        response = requests.get("http://localhost:8000/students")
        if response.status_code == 200:
            students_data = response.json()
            students = students_data["students"]
            
            st.success(f"✅ Found {len(students)} students in the assessment")
            
            # Display students in columns
            cols = st.columns(3)
            for i, student in enumerate(students):
                with cols[i % 3]:
                    st.metric(f"Student {i+1}", student)
            
            # Student selection
            selected_student = st.selectbox("Select a student for detailed view", students)
            
            if st.button("📊 Get Student Details"):
                # Get mastery data for selected student
                mastery_response = requests.post(
                    "http://localhost:8000/ask",
                    json={
                        "student_name": selected_student,
                        "question": "What is this student's mastery level?"
                    }
                )
                
                if mastery_response.status_code == 200:
                    mastery_data = mastery_response.json()
                    mastery_summary = mastery_data.get("mastery_summary", {})
                    
                    st.subheader(f"📊 {selected_student}'s Performance")
                    
                    # Display mastery data
                    if "topic_mastery" in mastery_summary:
                        for topic in mastery_summary["topic_mastery"]:
                            topic_name = topic["topic"]
                            mastery_pct = topic["mastery_percentage"]
                            total_points = topic["total_points"]
                            max_points = topic["max_points"]
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Topic", topic_name)
                            with col2:
                                st.metric("Mastery", f"{mastery_pct:.1f}%")
                            with col3:
                                st.metric("Score", f"{total_points}/{max_points}")
                    
                    # Performance indicator
                    if mastery_pct >= 80:
                        st.success("🎉 Excellent performance!")
                    elif mastery_pct >= 60:
                        st.info("👍 Good performance, room for improvement")
                    else:
                        st.warning("⚠️ Needs additional support")
                        
        else:
            st.error("❌ Could not connect to API")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the backend API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_ai_insights():
    st.header("🤖 AI-Powered Insights")
    
    # Get students from API
    try:
        response = requests.get("http://localhost:8000/students")
        if response.status_code == 200:
            students_data = response.json()
            students = students_data["students"]
            
            # Student selection
            selected_student = st.selectbox("Select a student", students)
            
            # Question input
            question = st.text_area(
                "Ask a question about this student's performance:",
                placeholder="e.g., What interventions would help this student? What are their strengths?",
                height=100
            )
            
            if st.button("🤖 Get AI Insights", type="primary"):
                if question.strip():
                    with st.spinner("Getting AI insights..."):
                        try:
                            ai_response = requests.post(
                                "http://localhost:8000/ask",
                                json={
                                    "student_name": selected_student,
                                    "question": question
                                }
                            )
                            
                            if ai_response.status_code == 200:
                                ai_data = ai_response.json()
                                
                                # Display mastery summary
                                mastery_summary = ai_data.get("mastery_summary", {})
                                if mastery_summary:
                                    st.subheader("📊 Current Performance")
                                    
                                    if "topic_mastery" in mastery_summary:
                                        for topic in mastery_summary["topic_mastery"]:
                                            topic_name = topic["topic"]
                                            mastery_pct = topic["mastery_percentage"]
                                            
                                            st.metric(
                                                f"{topic_name} Mastery",
                                                f"{mastery_pct:.1f}%"
                                            )
                                
                                # Display AI answer
                                st.subheader("🤖 AI Insights")
                                st.write(ai_data.get("answer", "No insights available"))
                                
                                # Display intervention plan if available
                                intervention_plan = ai_data.get("intervention_plan", "")
                                if intervention_plan and intervention_plan != "Great job! This student is performing well across all areas and doesn't need specific interventions at this time.":
                                    st.subheader("📋 Intervention Plan")
                                    st.write(intervention_plan)
                                    
                            else:
                                st.error(f"❌ API Error: {ai_response.status_code}")
                                
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Could not connect to the backend API")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a question")
                    
        else:
            st.error("❌ Could not connect to API")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the backend API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_performance_analysis():
    st.header("📈 Performance Analysis")
    
    # Get students and their performance
    try:
        response = requests.get("http://localhost:8000/students")
        if response.status_code == 200:
            students_data = response.json()
            students = students_data["students"]
            
            st.subheader("📊 Class Performance Overview")
            
            # Get performance data for all students
            performance_data = []
            
            with st.spinner("Loading performance data..."):
                for student in students:
                    try:
                        mastery_response = requests.post(
                            "http://localhost:8000/ask",
                            json={
                                "student_name": student,
                                "question": "What is this student's mastery level?"
                            }
                        )
                        
                        if mastery_response.status_code == 200:
                            mastery_data = mastery_response.json()
                            mastery_summary = mastery_data.get("mastery_summary", {})
                            
                            if "topic_mastery" in mastery_summary:
                                for topic in mastery_summary["topic_mastery"]:
                                    performance_data.append({
                                        "Student": student,
                                        "Topic": topic["topic"],
                                        "Mastery %": topic["mastery_percentage"],
                                        "Score": topic["total_points"],
                                        "Max Score": topic["max_points"]
                                    })
                    except:
                        continue
            
            if performance_data:
                # Create DataFrame
                df = pd.DataFrame(performance_data)
                
                # Display summary statistics
                st.subheader("📊 Summary Statistics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_mastery = df["Mastery %"].mean()
                    st.metric("Average Mastery", f"{avg_mastery:.1f}%")
                
                with col2:
                    max_mastery = df["Mastery %"].max()
                    st.metric("Highest Mastery", f"{max_mastery:.1f}%")
                
                with col3:
                    min_mastery = df["Mastery %"].min()
                    st.metric("Lowest Mastery", f"{min_mastery:.1f}%")
                
                # Display performance table
                st.subheader("📋 Student Performance Table")
                st.dataframe(df, use_container_width=True)
                
                # Performance categories
                st.subheader("🏆 Performance Categories")
                
                excellent = df[df["Mastery %"] >= 80]["Student"].unique()
                good = df[(df["Mastery %"] >= 60) & (df["Mastery %"] < 80)]["Student"].unique()
                needs_help = df[df["Mastery %"] < 60]["Student"].unique()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🎉 Excellent (80%+)", len(excellent))
                    if len(excellent) > 0:
                        for student in excellent:
                            st.write(f"• {student}")
                
                with col2:
                    st.metric("👍 Good (60-79%)", len(good))
                    if len(good) > 0:
                        for student in good:
                            st.write(f"• {student}")
                
                with col3:
                    st.metric("⚠️ Needs Help (<60%)", len(needs_help))
                    if len(needs_help) > 0:
                        for student in needs_help:
                            st.write(f"• {student}")
            else:
                st.warning("No performance data available")
                
        else:
            st.error("❌ Could not connect to API")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the backend API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
