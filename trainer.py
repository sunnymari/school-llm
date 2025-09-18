#!/usr/bin/env python3
"""
Assessment Trainer
Trains models and generates insights from assessment data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Response, ItemSchema, TopicMastery, StandardMastery
from app.score import get_student_mastery

class AssessmentTrainer:
    """Train models and generate insights from assessment data."""
    
    def __init__(self):
        self.models = {}
        self.feature_importance = {}
        self.predictions = {}
        
    def load_training_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load training data from database."""
        db: Session = SessionLocal()
        
        try:
            # Load responses
            responses_data = []
            for response in db.query(Response).all():
                responses_data.append({
                    'student': response.student,
                    'q1': response.q1, 'q2': response.q2, 'q3': response.q3,
                    'q4': response.q4, 'q5': response.q5, 'q6': response.q6,
                    'q7': response.q7, 'q8': response.q8, 'q9': response.q9, 'q10': response.q10
                })
            
            responses_df = pd.DataFrame(responses_data)
            
            # Load schema
            schema_data = []
            for schema in db.query(ItemSchema).all():
                schema_data.append({
                    'question': schema.question,
                    'topic': schema.topic,
                    'standard': schema.standard,
                    'max_points': schema.max_points
                })
            
            schema_df = pd.DataFrame(schema_data)
            
            # Load mastery data
            mastery_data = []
            for mastery in db.query(TopicMastery).all():
                mastery_data.append({
                    'student': mastery.student,
                    'topic': mastery.topic,
                    'mastery_percentage': mastery.mastery_percentage
                })
            
            mastery_df = pd.DataFrame(mastery_data)
            
            return responses_df, schema_df, mastery_df
            
        finally:
            db.close()
    
    def prepare_features(self, responses_df: pd.DataFrame, schema_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for training."""
        # Calculate topic scores for each student
        features = []
        
        for _, student in responses_df.iterrows():
            student_features = {'student': student['student']}
            
            # Add individual question scores
            for i in range(1, 11):
                student_features[f'q{i}'] = student.get(f'q{i}', 0)
            
            # Calculate topic scores
            topic_scores = {}
            for _, schema in schema_df.iterrows():
                question = schema['question']
                topic = schema['topic']
                max_points = schema['max_points']
                
                if f'q{question}' in student_features:
                    score = student_features[f'q{question}']
                    if topic not in topic_scores:
                        topic_scores[topic] = {'total': 0, 'max': 0}
                    topic_scores[topic]['total'] += score
                    topic_scores[topic]['max'] += max_points
            
            # Add topic mastery percentages
            for topic, scores in topic_scores.items():
                mastery = (scores['total'] / scores['max']) * 100 if scores['max'] > 0 else 0
                student_features[f'{topic}_mastery'] = mastery
            
            features.append(student_features)
        
        return pd.DataFrame(features)
    
    def train_mastery_predictor(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Train a model to predict overall mastery."""
        # Create target variable (overall mastery)
        topic_columns = [col for col in features_df.columns if col.endswith('_mastery')]
        features_df['overall_mastery'] = features_df[topic_columns].mean(axis=1)
        
        # Categorize mastery levels
        features_df['mastery_level'] = pd.cut(
            features_df['overall_mastery'],
            bins=[0, 60, 80, 100],
            labels=['Low', 'Medium', 'High']
        )
        
        # Prepare features (exclude student name and target variables)
        feature_columns = [col for col in features_df.columns 
                          if col not in ['student', 'overall_mastery', 'mastery_level']]
        
        X = features_df[feature_columns]
        y = features_df['mastery_level']
        
        # Handle NaN values
        X = X.fillna(0)
        y = y.dropna()
        
        # Ensure X and y have same length after dropping NaN
        if len(X) != len(y):
            # Remove rows from X where y is NaN
            valid_indices = features_df['mastery_level'].notna()
            X = X[valid_indices]
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Get feature importance
        importance = dict(zip(feature_columns, model.feature_importances_))
        
        # Make predictions
        predictions = model.predict(X)
        accuracy = accuracy_score(y, predictions)
        
        self.models['mastery_predictor'] = model
        self.feature_importance['mastery_predictor'] = importance
        
        return {
            'model': model,
            'accuracy': accuracy,
            'feature_importance': importance,
            'predictions': predictions.tolist()
        }
    
    def train_topic_predictor(self, features_df: pd.DataFrame, target_topic: str) -> Dict[str, Any]:
        """Train a model to predict performance in a specific topic."""
        topic_mastery_col = f'{target_topic}_mastery'
        
        if topic_mastery_col not in features_df.columns:
            return {'error': f'Topic {target_topic} not found in data'}
        
        # Prepare features
        feature_columns = [col for col in features_df.columns 
                          if col not in ['student', 'overall_mastery', 'mastery_level', topic_mastery_col]]
        
        X = features_df[feature_columns]
        y = features_df[topic_mastery_col]
        
        # Handle NaN values
        X = X.fillna(0)
        y = y.fillna(0)
        
        # Train regression model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Get feature importance
        importance = dict(zip(feature_columns, model.feature_importances_))
        
        # Make predictions
        predictions = model.predict(X)
        mse = mean_squared_error(y, predictions)
        
        model_key = f'topic_predictor_{target_topic}'
        self.models[model_key] = model
        self.feature_importance[model_key] = importance
        
        return {
            'model': model,
            'mse': mse,
            'feature_importance': importance,
            'predictions': predictions.tolist()
        }
    
    def generate_insights(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate insights from the training data."""
        insights = {}
        
        # Overall performance insights
        topic_columns = [col for col in features_df.columns if col.endswith('_mastery')]
        overall_mastery = features_df[topic_columns].mean(axis=1)
        
        insights['overall_stats'] = {
            'mean_mastery': float(overall_mastery.mean()),
            'std_mastery': float(overall_mastery.std()),
            'min_mastery': float(overall_mastery.min()),
            'max_mastery': float(overall_mastery.max())
        }
        
        # Topic difficulty analysis
        topic_difficulty = {}
        for topic_col in topic_columns:
            topic_name = topic_col.replace('_mastery', '')
            topic_difficulty[topic_name] = {
                'mean_mastery': float(features_df[topic_col].mean()),
                'std_mastery': float(features_df[topic_col].std())
            }
        
        insights['topic_difficulty'] = topic_difficulty
        
        # Student performance patterns
        high_performers = features_df[overall_mastery >= 80]['student'].tolist()
        low_performers = features_df[overall_mastery < 60]['student'].tolist()
        
        insights['performance_groups'] = {
            'high_performers': high_performers,
            'low_performers': low_performers,
            'high_performer_count': len(high_performers),
            'low_performer_count': len(low_performers)
        }
        
        return insights
    
    def predict_student_performance(self, student_name: str, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Predict performance for a specific student."""
        student_data = features_df[features_df['student'] == student_name]
        
        if student_data.empty:
            return {'error': f'Student {student_name} not found'}
        
        predictions = {}
        
        # Predict overall mastery level
        if 'mastery_predictor' in self.models:
            feature_columns = [col for col in features_df.columns 
                              if col not in ['student', 'overall_mastery', 'mastery_level']]
            X = student_data[feature_columns]
            mastery_prediction = self.models['mastery_predictor'].predict(X)[0]
            predictions['overall_mastery_level'] = mastery_prediction
        
        # Predict topic performance
        topic_columns = [col for col in features_df.columns if col.endswith('_mastery')]
        for topic_col in topic_columns:
            topic_name = topic_col.replace('_mastery', '')
            model_key = f'topic_predictor_{topic_name}'
            
            if model_key in self.models:
                feature_columns = [col for col in features_df.columns 
                                  if col not in ['student', 'overall_mastery', 'mastery_level', topic_col]]
                X = student_data[feature_columns]
                topic_prediction = self.models[model_key].predict(X)[0]
                predictions[f'{topic_name}_prediction'] = float(topic_prediction)
        
        return predictions
    
    def save_models(self, models_dir: str = "./models"):
        """Save trained models to disk."""
        os.makedirs(models_dir, exist_ok=True)
        
        for model_name, model in self.models.items():
            model_path = os.path.join(models_dir, f"{model_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        # Save feature importance
        importance_path = os.path.join(models_dir, "feature_importance.pkl")
        with open(importance_path, 'wb') as f:
            pickle.dump(self.feature_importance, f)
        
        print(f"💾 Models saved to {models_dir}")
    
    def load_models(self, models_dir: str = "./models"):
        """Load trained models from disk."""
        if not os.path.exists(models_dir):
            print(f"❌ Models directory {models_dir} not found")
            return False
        
        # Load models
        for file in os.listdir(models_dir):
            if file.endswith('.pkl') and file != 'feature_importance.pkl':
                model_name = file.replace('.pkl', '')
                model_path = os.path.join(models_dir, file)
                with open(model_path, 'rb') as f:
                    self.models[model_name] = pickle.load(f)
        
        # Load feature importance
        importance_path = os.path.join(models_dir, "feature_importance.pkl")
        if os.path.exists(importance_path):
            with open(importance_path, 'rb') as f:
                self.feature_importance = pickle.load(f)
        
        print(f"📂 Models loaded from {models_dir}")
        return True
    
    def train_all_models(self) -> Dict[str, Any]:
        """Train all models and generate insights."""
        print("🤖 Training Assessment Models")
        print("=" * 50)
        
        # Load data
        responses_df, schema_df, mastery_df = self.load_training_data()
        
        if responses_df.empty:
            return {'error': 'No training data available'}
        
        print(f"📊 Training data: {len(responses_df)} students, {len(schema_df)} questions")
        
        # Prepare features
        features_df = self.prepare_features(responses_df, schema_df)
        print(f"🔧 Features prepared: {features_df.shape}")
        
        # Train models
        results = {}
        
        # Train overall mastery predictor
        print("🎯 Training overall mastery predictor...")
        mastery_result = self.train_mastery_predictor(features_df)
        results['mastery_predictor'] = mastery_result
        print(f"   Accuracy: {mastery_result['accuracy']:.3f}")
        
        # Train topic-specific predictors
        topic_columns = [col for col in features_df.columns if col.endswith('_mastery')]
        for topic_col in topic_columns:
            topic_name = topic_col.replace('_mastery', '')
            print(f"📚 Training {topic_name} predictor...")
            topic_result = self.train_topic_predictor(features_df, topic_name)
            results[f'topic_{topic_name}'] = topic_result
            if 'mse' in topic_result:
                print(f"   MSE: {topic_result['mse']:.3f}")
        
        # Generate insights
        print("💡 Generating insights...")
        insights = self.generate_insights(features_df)
        results['insights'] = insights
        
        # Save models
        self.save_models()
        
        print("✅ Training completed successfully!")
        return results

def main():
    """Main function for command line usage."""
    trainer = AssessmentTrainer()
    results = trainer.train_all_models()
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
    else:
        print("🎉 Training completed successfully!")
        print(f"📊 Trained {len(trainer.models)} models")
        print(f"💡 Generated insights for {len(results['insights']['topic_difficulty'])} topics")

if __name__ == "__main__":
    main()
