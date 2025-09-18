#!/usr/bin/env python3
"""
Process Your Specific Assessment Data
Custom processor for your assessment_scores format.
"""

import pandas as pd
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app.models import Base, ItemSchema, Response
from app.score import compute_aggregates

def process_your_assessment_data():
    """Process your specific assessment data format."""
    print("🔄 Processing Your Assessment Data")
    print("=" * 50)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Clear existing data
        db.query(ItemSchema).delete()
        db.query(Response).delete()
        db.commit()
        
        # Load and process schema
        print("📊 Loading schema...")
        schema_df = pd.read_csv("./assessment_scores/assessment_schema.csv")
        
        # Only use questions 1-3 since that's what you have data for
        schema_subset = schema_df[schema_df['Question'].isin([1, 2, 3])]
        
        for _, row in schema_subset.iterrows():
            schema_item = ItemSchema(
                question=int(row['Question']),
                prompt_stub=str(row['PromptStub']),
                topic=str(row['Topic']),
                standard=str(row['Standard']),
                max_points=float(row['MaxPoints'])
            )
            db.add(schema_item)
        
        db.commit()
        print(f"✅ Loaded schema: {len(schema_subset)} questions")
        
        # Load and process responses
        print("📊 Loading student responses...")
        responses_df = pd.read_csv("./assessment_scores/assessment_scores.csv")
        
        for _, row in responses_df.iterrows():
            student_name = str(row['Name'])
            
            # Create response object
            response = Response(student=student_name)
            
            # Map your specific columns to Q1, Q2, Q3
            response.q1 = float(row['Q1_8cubes']) if not pd.isna(row['Q1_8cubes']) else 0.0
            response.q2 = float(row['Q2_6cubes']) if not pd.isna(row['Q2_6cubes']) else 0.0
            response.q3 = float(row['Q3_morecubes']) if not pd.isna(row['Q3_morecubes']) else 0.0
            
            # Set remaining questions to 0 (not applicable)
            response.q4 = 0.0
            response.q5 = 0.0
            response.q6 = 0.0
            response.q7 = 0.0
            response.q8 = 0.0
            response.q9 = 0.0
            response.q10 = 0.0
            
            db.add(response)
        
        db.commit()
        print(f"✅ Loaded responses: {len(responses_df)} students")
        
        # Compute mastery scores
        print("🧮 Computing mastery scores...")
        compute_aggregates(db)
        print("✅ Mastery scores computed")
        
        # Show summary
        print("\n📊 Data Summary:")
        print(f"   Students: {len(responses_df)}")
        print(f"   Questions: {len(schema_subset)}")
        print(f"   Topics: {schema_subset['Topic'].nunique()}")
        
        # Show student list
        print("\n👥 Students loaded:")
        for student in responses_df['Name']:
            print(f"   • {student}")
        
        print("\n🎉 Your assessment data has been successfully loaded!")
        
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    process_your_assessment_data()
