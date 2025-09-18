#!/usr/bin/env python3
"""
Train Assessment Models
Trains machine learning models on assessment data.
"""

from app.trainer import AssessmentTrainer
import sys

def main():
    print("🤖 Training assessment models...")
    
    # Create trainer
    trainer = AssessmentTrainer()
    
    # Train all models
    results = trainer.train_all_models()
    
    if 'error' in results:
        print(f"❌ Training failed: {results['error']}")
        sys.exit(1)
    else:
        print("✅ Model training completed successfully!")
        
        # Show results
        if 'mastery_predictor' in results:
            accuracy = results['mastery_predictor']['accuracy']
            print(f"🎯 Mastery Predictor Accuracy: {accuracy:.3f}")
        
        # Count topic models
        topic_models = [k for k in results.keys() if k.startswith('topic_')]
        print(f"📚 Trained {len(topic_models)} topic-specific models")
        
        # Show insights
        if 'insights' in results:
            insights = results['insights']
            print(f"📊 Generated insights for {len(insights['topic_difficulty'])} topics")
            print(f"👥 Identified {insights['performance_groups']['high_performer_count']} high performers")
            print(f"👥 Identified {insights['performance_groups']['low_performer_count']} low performers")

if __name__ == "__main__":
    main()
