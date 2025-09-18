#!/usr/bin/env python3
"""
Simple script to run the assessment system with real data
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_assessment_data():
    """Analyze the assessment data and create summary statistics"""
    
    # Load the data
    df = pd.read_csv('data/responses.csv')
    schema_df = pd.read_csv('data/assessment_schema.csv')
    
    print("🧮 MATH ASSESSMENT ANALYSIS")
    print("=" * 50)
    
    # Basic statistics
    print(f"📊 Total Students: {len(df)}")
    print(f"📝 Total Questions: {len(schema_df)}")
    print(f"📈 Average Score: {df['Total'].mean():.1f} out of {df['Total'].max()}")
    print(f"🎯 Highest Score: {df['Total'].max()}")
    print(f"📉 Lowest Score: {df['Total'].min()}")
    
    # Student performance breakdown
    print("\n👥 STUDENT PERFORMANCE:")
    print("-" * 30)
    
    for _, row in df.iterrows():
        name = row['Name']
        total = row['Total']
        percentage = (total / 3) * 100
        
        # Performance level
        if percentage >= 80:
            level = "🎉 Excellent"
        elif percentage >= 60:
            level = "👍 Good"
        else:
            level = "📚 Needs Support"
        
        print(f"{name:<15} {total}/3 ({percentage:4.0f}%) {level}")
    
    # Question analysis
    print("\n❓ QUESTION ANALYSIS:")
    print("-" * 30)
    
    questions = ['Q1_8cubes', 'Q2_6cubes', 'Q3_morecubes']
    question_names = ['8 Cubes', '6 Cubes', 'More Cubes']
    
    for q, name in zip(questions, question_names):
        correct = df[q].sum()
        total_students = len(df)
        percentage = (correct / total_students) * 100
        
        print(f"{name:<12} {correct}/{total_students} ({percentage:4.0f}% correct)")
    
    # Mastery levels
    print("\n🎯 MASTERY LEVELS:")
    print("-" * 30)
    
    mastery_counts = {
        "Mastered (3/3)": len(df[df['Total'] == 3]),
        "Developing (2/3)": len(df[df['Total'] == 2]),
        "Beginning (1/3)": len(df[df['Total'] == 1]),
        "Needs Support (0/3)": len(df[df['Total'] == 0])
    }
    
    for level, count in mastery_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{level:<20} {count} students ({percentage:4.0f}%)")
    
    return df

def create_intervention_recommendations(df):
    """Create intervention recommendations based on performance"""
    
    print("\n💡 INTERVENTION RECOMMENDATIONS:")
    print("=" * 50)
    
    # Students who need support
    struggling_students = df[df['Total'] < 2]
    
    if len(struggling_students) > 0:
        print(f"📚 Students needing additional support ({len(struggling_students)}):")
        for _, student in struggling_students.iterrows():
            name = student['Name']
            score = student['Total']
            
            recommendations = []
            if student['Q1_8cubes'] == 0:
                recommendations.append("Practice counting to 8")
            if student['Q2_6cubes'] == 0:
                recommendations.append("Practice counting to 6")
            if student['Q3_morecubes'] == 0:
                recommendations.append("Practice comparing quantities")
            
            print(f"  • {name} ({score}/3): {', '.join(recommendations)}")
    
    # High performers
    high_performers = df[df['Total'] == 3]
    if len(high_performers) > 0:
        print(f"\n🌟 High performers ({len(high_performers)}):")
        for _, student in high_performers.iterrows():
            print(f"  • {student['Name']}: Ready for advanced counting activities")

if __name__ == "__main__":
    # Analyze the data
    df = analyze_assessment_data()
    
    # Create recommendations
    create_intervention_recommendations(df)
    
    print("\n✅ Assessment analysis complete!")
    print("\n🚀 To run the interactive dashboard:")
    print("   streamlit run simple_dashboard.py")
