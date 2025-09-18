#!/usr/bin/env python3
"""
Process Assessment Data from Folder
Reads assessment scores from a folder and loads them into the system.
"""

from app.data_processor import AssessmentDataProcessor
import sys
import os

def main():
    # Get folder path from command line or use default
    if len(sys.argv) > 1:
        data_folder = sys.argv[1]
    else:
        data_folder = "./assessment_scores"
    
    print(f"🔄 Processing assessment data from: {data_folder}")
    
    # Create processor
    processor = AssessmentDataProcessor(data_folder)
    
    # Process all files
    results = processor.process_all_files()
    
    if results["success"]:
        print("✅ Assessment data processing completed successfully!")
        print(f"📊 Processed {results['processed']} files successfully")
        if results['failed'] > 0:
            print(f"⚠️  {results['failed']} files failed to process")
    else:
        print(f"❌ Processing failed: {results.get('message', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
