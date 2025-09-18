import streamlit as st
import pandas as pd
import os
import sys
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.data_processor import AssessmentDataProcessor
    from app.trainer import AssessmentTrainer
except ImportError:
    # Fallback: try importing from parent directory
    import importlib.util
    import sys
    
    # Add parent directory to path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    # Import modules
    from app.data_processor import AssessmentDataProcessor
    from app.trainer import AssessmentTrainer

# Configure page
st.set_page_config(
    page_title="Assessment Trainer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 Assessment Data Trainer")
    st.markdown("Upload assessment data from a folder and train ML models for insights!")
    
    # Sidebar for navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📁 Data Processing", 
        "🤖 Model Training", 
        "📊 Insights & Predictions",
        "📈 Performance Analysis"
    ])
    
    if page == "📁 Data Processing":
        show_data_processing()
    elif page == "🤖 Model Training":
        show_model_training()
    elif page == "📊 Insights & Predictions":
        show_insights()
    elif page == "📈 Performance Analysis":
        show_performance_analysis()

def show_data_processing():
    st.header("📁 Assessment Data Processing")
    
    # Data folder input
    st.subheader("📂 Assessment Scores Folder")
    data_folder = st.text_input(
        "Path to assessment scores folder",
        value="./assessment_scores",
        help="Folder containing CSV/Excel files with assessment data"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Scan Folder", type="primary"):
            processor = AssessmentDataProcessor(data_folder)
            files = processor.scan_for_files()
            
            if files:
                st.success(f"Found {len(files)} files:")
                for file in files:
                    st.write(f"📄 {file.name}")
            else:
                st.warning("No assessment files found in folder")
                st.info("Supported formats: .csv, .xlsx, .json, .tsv")
    
    with col2:
        if st.button("📁 Create Sample Files"):
            processor = AssessmentDataProcessor(data_folder)
            processor.create_sample_files()
            st.success("Sample files created!")
    
    # Process files
    if st.button("🔄 Process All Files", type="primary"):
        with st.spinner("Processing assessment files..."):
            processor = AssessmentDataProcessor(data_folder)
            results = processor.process_all_files()
            
            if results["success"]:
                st.success("✅ Data processing completed!")
                
                # Show results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Files Processed", results["processed"])
                with col2:
                    st.metric("Files Failed", results["failed"])
                with col3:
                    st.metric("Success Rate", f"{(results['processed']/(results['processed']+results['failed'])*100):.1f}%")
                
                # Show file details
                if results["files"]:
                    st.subheader("📄 File Processing Details")
                    file_df = pd.DataFrame(results["files"])
                    st.dataframe(file_df, use_container_width=True)
            else:
                st.error(f"❌ Processing failed: {results.get('message', 'Unknown error')}")
    
    # File upload section
    st.subheader("📤 Upload Assessment Files")
    
    uploaded_files = st.file_uploader(
        "Upload assessment files",
        type=['csv', 'xlsx', 'json'],
        accept_multiple_files=True,
        help="Upload schema, response, or intervention files"
    )
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} files:")
        for file in uploaded_files:
            st.write(f"📄 {file.name}")
        
        if st.button("💾 Save Uploaded Files"):
            processor = AssessmentDataProcessor(data_folder)
            processor.create_data_folder()
            
            saved_files = []
            for uploaded_file in uploaded_files:
                file_path = processor.data_folder / uploaded_file.name
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)
            
            st.success(f"✅ Saved {len(saved_files)} files to {data_folder}")

def show_model_training():
    st.header("🤖 Model Training")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Training Options")
        
        train_mastery = st.checkbox("Train Overall Mastery Predictor", value=True)
        train_topics = st.checkbox("Train Topic-Specific Predictors", value=True)
        
        if st.button("🚀 Start Training", type="primary"):
            with st.spinner("Training models..."):
                trainer = AssessmentTrainer()
                results = trainer.train_all_models()
                
                if 'error' in results:
                    st.error(f"❌ Training failed: {results['error']}")
                else:
                    st.success("✅ Training completed successfully!")
                    
                    # Show training results
                    if 'mastery_predictor' in results:
                        mastery_acc = results['mastery_predictor']['accuracy']
                        st.metric("Mastery Predictor Accuracy", f"{mastery_acc:.3f}")
                    
                    # Show topic results
                    topic_results = {k: v for k, v in results.items() if k.startswith('topic_')}
                    if topic_results:
                        st.subheader("📚 Topic Predictors")
                        for topic, result in topic_results.items():
                            if 'mse' in result:
                                topic_name = topic.replace('topic_', '')
                                st.metric(f"{topic_name.title()} MSE", f"{result['mse']:.3f}")
    
    with col2:
        st.subheader("📊 Model Information")
        
        # Check if models exist
        models_dir = Path("./models")
        if models_dir.exists():
            model_files = list(models_dir.glob("*.pkl"))
            st.write(f"📁 Found {len(model_files)} trained models:")
            for model_file in model_files:
                st.write(f"🤖 {model_file.stem}")
        else:
            st.info("No trained models found. Run training first.")
        
        # Load existing models
        if st.button("📂 Load Existing Models"):
            trainer = AssessmentTrainer()
            if trainer.load_models():
                st.success("✅ Models loaded successfully!")
                st.session_state.trainer = trainer
            else:
                st.error("❌ Failed to load models")

def show_insights():
    st.header("📊 Insights & Predictions")
    
    # Load trainer if available
    if 'trainer' not in st.session_state:
        trainer = AssessmentTrainer()
        if trainer.load_models():
            st.session_state.trainer = trainer
        else:
            st.warning("No trained models found. Please train models first.")
            return
    
    trainer = st.session_state.trainer
    
    # Student prediction
    st.subheader("🎯 Student Performance Prediction")
    
    # Get available students
    try:
        from app.db import SessionLocal
        from app.models import Response
        
        db = SessionLocal()
        students = [r.student for r in db.query(Response.student).distinct().all()]
        db.close()
        
        if students:
            selected_student = st.selectbox("Select a student", students)
            
            if st.button("🔮 Predict Performance"):
                # Load features for prediction
                responses_df, schema_df, mastery_df = trainer.load_training_data()
                features_df = trainer.prepare_features(responses_df, schema_df)
                
                predictions = trainer.predict_student_performance(selected_student, features_df)
                
                if 'error' in predictions:
                    st.error(predictions['error'])
                else:
                    st.success(f"📊 Predictions for {selected_student}:")
                    
                    # Display predictions
                    for key, value in predictions.items():
                        if isinstance(value, str):
                            st.write(f"**{key.replace('_', ' ').title()}**: {value}")
                        else:
                            st.metric(key.replace('_', ' ').title(), f"{value:.2f}")
        else:
            st.warning("No students found in database")
    except Exception as e:
        st.error(f"Error loading students: {str(e)}")
    
    # Feature importance
    st.subheader("🔍 Feature Importance")
    
    if trainer.feature_importance:
        for model_name, importance in trainer.feature_importance.items():
            if importance:
                st.write(f"**{model_name.replace('_', ' ').title()}**")
                
                # Sort features by importance
                sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                
                # Create bar chart
                features, scores = zip(*sorted_features[:10])  # Top 10 features
                
                fig = px.bar(
                    x=list(scores),
                    y=list(features),
                    orientation='h',
                    title=f"Top 10 Features - {model_name}",
                    labels={'x': 'Importance', 'y': 'Feature'}
                )
                st.plotly_chart(fig, use_container_width=True)

def show_performance_analysis():
    st.header("📈 Performance Analysis")
    
    try:
        # Load data for analysis
        trainer = AssessmentTrainer()
        responses_df, schema_df, mastery_df = trainer.load_training_data()
        
        if responses_df.empty:
            st.warning("No data available for analysis")
            return
        
        features_df = trainer.prepare_features(responses_df, schema_df)
        insights = trainer.generate_insights(features_df)
        
        # Overall statistics
        st.subheader("📊 Overall Performance Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean Mastery", f"{insights['overall_stats']['mean_mastery']:.1f}%")
        with col2:
            st.metric("Std Deviation", f"{insights['overall_stats']['std_mastery']:.1f}%")
        with col3:
            st.metric("Min Mastery", f"{insights['overall_stats']['min_mastery']:.1f}%")
        with col4:
            st.metric("Max Mastery", f"{insights['overall_stats']['max_mastery']:.1f}%")
        
        # Topic difficulty analysis
        st.subheader("📚 Topic Difficulty Analysis")
        
        topic_data = []
        for topic, stats in insights['topic_difficulty'].items():
            topic_data.append({
                'Topic': topic,
                'Mean Mastery': stats['mean_mastery'],
                'Std Deviation': stats['std_mastery']
            })
        
        topic_df = pd.DataFrame(topic_data)
        topic_df = topic_df.sort_values('Mean Mastery')
        
        # Topic difficulty chart
        fig = px.bar(
            topic_df,
            x='Topic',
            y='Mean Mastery',
            title='Average Mastery by Topic',
            labels={'Mean Mastery': 'Average Mastery (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance groups
        st.subheader("👥 Performance Groups")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("High Performers", insights['performance_groups']['high_performer_count'])
            if insights['performance_groups']['high_performers']:
                st.write("**High Performers:**")
                for student in insights['performance_groups']['high_performers']:
                    st.write(f"• {student}")
        
        with col2:
            st.metric("Low Performers", insights['performance_groups']['low_performer_count'])
            if insights['performance_groups']['low_performers']:
                st.write("**Low Performers:**")
                for student in insights['performance_groups']['low_performers']:
                    st.write(f"• {student}")
        
        # Student performance distribution
        st.subheader("📊 Student Performance Distribution")
        
        topic_columns = [col for col in features_df.columns if col.endswith('_mastery')]
        overall_mastery = features_df[topic_columns].mean(axis=1)
        
        fig = px.histogram(
            x=overall_mastery,
            nbins=20,
            title='Distribution of Overall Mastery Scores',
            labels={'x': 'Overall Mastery (%)', 'y': 'Number of Students'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error in performance analysis: {str(e)}")

if __name__ == "__main__":
    main()
