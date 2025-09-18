#!/usr/bin/env python3
"""
Data Processor for Assessment Scores
Reads assessment data from various file formats and processes them for training.
"""

import pandas as pd
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlite3
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app.models import Base, ItemSchema, Response
from app.score import compute_aggregates

class AssessmentDataProcessor:
    """Process assessment data from various sources."""
    
    def __init__(self, data_folder: str = "./assessment_scores"):
        self.data_folder = Path(data_folder)
        self.supported_formats = ['.csv', '.xlsx', '.json', '.tsv']
        self.processed_files = []
        
    def create_data_folder(self):
        """Create the assessment scores folder if it doesn't exist."""
        self.data_folder.mkdir(exist_ok=True)
        print(f"📁 Assessment scores folder: {self.data_folder}")
        
    def scan_for_files(self) -> List[Path]:
        """Scan the data folder for assessment files."""
        if not self.data_folder.exists():
            return []
            
        files = []
        for format_ext in self.supported_formats:
            files.extend(self.data_folder.glob(f"*{format_ext}"))
            
        return files
    
    def detect_file_type(self, file_path: Path) -> str:
        """Detect the type of assessment file."""
        filename = file_path.name.lower()
        
        if 'schema' in filename or 'question' in filename:
            return 'schema'
        elif 'response' in filename or 'answer' in filename or 'score' in filename:
            return 'response'
        elif 'intervention' in filename or 'strategy' in filename:
            return 'intervention'
        else:
            return 'unknown'
    
    def load_csv_file(self, file_path: Path) -> pd.DataFrame:
        """Load CSV file with various delimiters."""
        try:
            # Try comma first
            df = pd.read_csv(file_path)
            if len(df.columns) == 1:
                # Try tab delimiter
                df = pd.read_csv(file_path, sep='\t')
            if len(df.columns) == 1:
                # Try semicolon delimiter
                df = pd.read_csv(file_path, sep=';')
            return df
        except Exception as e:
            print(f"Error loading CSV {file_path}: {e}")
            return pd.DataFrame()
    
    def load_excel_file(self, file_path: Path) -> pd.DataFrame:
        """Load Excel file."""
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"Error loading Excel {file_path}: {e}")
            return pd.DataFrame()
    
    def load_json_file(self, file_path: Path) -> pd.DataFrame:
        """Load JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading JSON {file_path}: {e}")
            return pd.DataFrame()
    
    def load_file(self, file_path: Path) -> pd.DataFrame:
        """Load file based on extension."""
        extension = file_path.suffix.lower()
        
        if extension == '.csv':
            return self.load_csv_file(file_path)
        elif extension == '.xlsx':
            return self.load_excel_file(file_path)
        elif extension == '.json':
            return self.load_json_file(file_path)
        elif extension == '.tsv':
            return pd.read_csv(file_path, sep='\t')
        else:
            print(f"Unsupported file format: {extension}")
            return pd.DataFrame()
    
    def validate_schema_data(self, df: pd.DataFrame) -> bool:
        """Validate schema data format."""
        required_columns = ['Question', 'Topic', 'Standard', 'MaxPoints']
        optional_columns = ['PromptStub', 'Prompt', 'QuestionText']
        
        # Check for required columns
        if not all(col in df.columns for col in required_columns):
            print(f"Schema missing required columns: {required_columns}")
            return False
            
        # Check for question numbers
        if not pd.api.types.is_numeric_dtype(df['Question']):
            print("Question column must contain numeric values")
            return False
            
        return True
    
    def validate_response_data(self, df: pd.DataFrame) -> bool:
        """Validate response data format."""
        # Look for student identifier column
        student_cols = [col for col in df.columns if 'student' in col.lower() or 'name' in col.lower()]
        if not student_cols:
            print("No student identifier column found (looking for 'student' or 'name')")
            return False
            
        # Look for question columns - handle both Q1, Q2 format and Q1_8cubes format
        question_cols = []
        for col in df.columns:
            if col.startswith(('Q', 'q')):
                # Check if it's Q1, Q2, Q3 format
                if col[1:].isdigit():
                    question_cols.append(col)
                # Check if it's Q1_something, Q2_something format
                elif '_' in col and col.split('_')[0][1:].isdigit():
                    question_cols.append(col)
        
        if not question_cols:
            print("No question columns found (looking for Q1, Q2, Q1_8cubes, etc.)")
            return False
            
        return True
    
    def process_schema_file(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Process schema file and load into database."""
        if not self.validate_schema_data(df):
            return False
            
        try:
            db: Session = SessionLocal()
            
            # Clear existing schema
            db.query(ItemSchema).delete()
            db.commit()
            
            # Insert new schema
            for _, row in df.iterrows():
                schema_item = ItemSchema(
                    question=int(row['Question']),
                    prompt_stub=str(row.get('PromptStub', row.get('Prompt', f"Question {row['Question']}"))),
                    topic=str(row['Topic']),
                    standard=str(row['Standard']),
                    max_points=float(row['MaxPoints'])
                )
                db.add(schema_item)
            
            db.commit()
            db.close()
            
            print(f"✅ Loaded schema from {file_path.name}: {len(df)} questions")
            return True
            
        except Exception as e:
            print(f"Error processing schema file {file_path}: {e}")
            return False
    
    def process_response_file(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Process response file and load into database."""
        if not self.validate_response_data(df):
            return False
            
        try:
            db: Session = SessionLocal()
            
            # Find student column
            student_col = [col for col in df.columns if 'student' in col.lower() or 'name' in col.lower()][0]
            
            # Find question columns - handle both formats
            question_cols = []
            for col in df.columns:
                if col.startswith(('Q', 'q')):
                    # Check if it's Q1, Q2, Q3 format
                    if col[1:].isdigit():
                        question_cols.append(col)
                    # Check if it's Q1_something, Q2_something format
                    elif '_' in col and col.split('_')[0][1:].isdigit():
                        question_cols.append(col)
            
            # Sort by question number
            question_cols.sort(key=lambda x: int(x.split('_')[0][1:]) if '_' in x else int(x[1:]))
            
            # Clear existing responses
            db.query(Response).delete()
            db.commit()
            
            # Process each student's responses
            for _, row in df.iterrows():
                student_name = str(row[student_col])
                
                # Create response object
                response = Response(student=student_name)
                
                # Map question columns to response fields
                for i, col in enumerate(question_cols, 1):
                    if i <= 10:  # Limit to Q1-Q10 for now
                        value = row[col]
                        if pd.isna(value) or value is None:
                            value = 0
                        try:
                            setattr(response, f'q{i}', float(value))
                        except (ValueError, TypeError):
                            setattr(response, f'q{i}', 0.0)
                
                db.add(response)
            
            db.commit()
            
            # Compute aggregates
            compute_aggregates(db)
            db.close()
            
            print(f"✅ Loaded responses from {file_path.name}: {len(df)} students")
            return True
            
        except Exception as e:
            print(f"Error processing response file {file_path}: {e}")
            return False
    
    def process_intervention_file(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Process intervention/strategy file."""
        try:
            # Convert to markdown format and save
            markdown_content = "# Educational Interventions\n\n"
            
            for _, row in df.iterrows():
                topic = row.get('Topic', row.get('Subject', 'General'))
                strategy = row.get('Strategy', row.get('Intervention', row.get('Content', '')))
                
                markdown_content += f"## {topic}\n{strategy}\n\n"
            
            # Save to interventions.md
            interventions_file = Path("./data/interventions.md")
            with open(interventions_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Processed interventions from {file_path.name}")
            return True
            
        except Exception as e:
            print(f"Error processing intervention file {file_path}: {e}")
            return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single assessment file."""
        print(f"\n📄 Processing: {file_path.name}")
        
        # Load file
        df = self.load_file(file_path)
        if df.empty:
            print(f"❌ Failed to load {file_path.name}")
            return False
        
        print(f"   Columns: {list(df.columns)}")
        print(f"   Rows: {len(df)}")
        
        # Detect file type
        file_type = self.detect_file_type(file_path)
        print(f"   Type: {file_type}")
        
        # Process based on type
        success = False
        if file_type == 'schema':
            success = self.process_schema_file(df, file_path)
        elif file_type == 'response':
            success = self.process_response_file(df, file_path)
        elif file_type == 'intervention':
            success = self.process_intervention_file(df, file_path)
        else:
            print(f"⚠️  Unknown file type, skipping {file_path.name}")
            return False
        
        if success:
            self.processed_files.append(file_path)
        
        return success
    
    def process_all_files(self) -> Dict[str, Any]:
        """Process all files in the assessment scores folder."""
        print("🔄 Processing Assessment Scores Folder")
        print("=" * 50)
        
        # Create folder if it doesn't exist
        self.create_data_folder()
        
        # Scan for files
        files = self.scan_for_files()
        
        if not files:
            print(f"📁 No assessment files found in {self.data_folder}")
            print("   Supported formats: .csv, .xlsx, .json, .tsv")
            print("   Expected files:")
            print("   - assessment_schema.csv (question definitions)")
            print("   - student_responses.csv (student scores)")
            print("   - interventions.csv (teaching strategies)")
            return {"success": False, "message": "No files found"}
        
        print(f"📊 Found {len(files)} files to process")
        
        # Process each file
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "files": []
        }
        
        for file_path in files:
            try:
                success = self.process_file(file_path)
                if success:
                    results["processed"] += 1
                    results["files"].append({"name": file_path.name, "status": "success"})
                else:
                    results["failed"] += 1
                    results["files"].append({"name": file_path.name, "status": "failed"})
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                results["failed"] += 1
                results["files"].append({"name": file_path.name, "status": "error", "error": str(e)})
        
        print("\n" + "=" * 50)
        print(f"📊 Processing Complete:")
        print(f"   ✅ Successfully processed: {results['processed']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        return results
    
    def create_sample_files(self):
        """Create sample assessment files for testing."""
        sample_folder = self.data_folder / "samples"
        sample_folder.mkdir(exist_ok=True)
        
        # Sample schema
        schema_data = {
            'Question': [1, 2, 3, 4, 5],
            'PromptStub': ['What is...?', 'Solve...', 'Define...', 'Explain...', 'Calculate...'],
            'Topic': ['Geography', 'Math', 'Science', 'History', 'Grammar'],
            'Standard': ['World Knowledge', 'Problem Solving', 'Scientific Method', 'Historical Analysis', 'Language Arts'],
            'MaxPoints': [2, 3, 4, 3, 2]
        }
        
        schema_df = pd.DataFrame(schema_data)
        schema_df.to_csv(sample_folder / "sample_schema.csv", index=False)
        
        # Sample responses
        response_data = {
            'Student': ['Alice', 'Bob', 'Charlie'],
            'Q1': [2, 1, 2],
            'Q2': [3, 2, 3],
            'Q3': [3, 2, 4],
            'Q4': [2, 1, 3],
            'Q5': [2, 1, 2]
        }
        
        response_df = pd.DataFrame(response_data)
        response_df.to_csv(sample_folder / "sample_responses.csv", index=False)
        
        # Sample interventions
        intervention_data = {
            'Topic': ['Math', 'Science', 'Geography'],
            'Strategy': ['Use visual aids', 'Hands-on experiments', 'Map exercises']
        }
        
        intervention_df = pd.DataFrame(intervention_data)
        intervention_df.to_csv(sample_folder / "sample_interventions.csv", index=False)
        
        print(f"📁 Sample files created in {sample_folder}")
        print("   - sample_schema.csv")
        print("   - sample_responses.csv") 
        print("   - sample_interventions.csv")

def main():
    """Main function for command line usage."""
    processor = AssessmentDataProcessor()
    
    # Create sample files if folder is empty
    files = processor.scan_for_files()
    if not files:
        print("Creating sample files...")
        processor.create_sample_files()
    
    # Process all files
    results = processor.process_all_files()
    
    if results["success"]:
        print("🎉 Assessment data processing completed successfully!")
    else:
        print("❌ Assessment data processing failed")

if __name__ == "__main__":
    main()
