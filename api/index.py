from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Math Assessment System", version="1.0.0")

# Sample data
SAMPLE_STUDENTS = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]

SAMPLE_MASTERY = {
    "Alice": {"Counting": 85, "Number Recognition": 90, "Overall": 87.5},
    "Bob": {"Counting": 70, "Number Recognition": 75, "Overall": 72.5},
    "Charlie": {"Counting": 95, "Number Recognition": 88, "Overall": 91.5},
    "Diana": {"Counting": 60, "Number Recognition": 65, "Overall": 62.5},
    "Eve": {"Counting": 80, "Number Recognition": 85, "Overall": 82.5},
    "Frank": {"Counting": 45, "Number Recognition": 50, "Overall": 47.5},
    "Grace": {"Counting": 90, "Number Recognition": 92, "Overall": 91.0},
    "Henry": {"Counting": 75, "Number Recognition": 70, "Overall": 72.5},
    "Ivy": {"Counting": 88, "Number Recognition": 85, "Overall": 86.5},
    "Jack": {"Counting": 55, "Number Recognition": 60, "Overall": 57.5}
}

@app.get("/")
async def root():
    return {
        "message": "Math Assessment System is running!",
        "students": SAMPLE_STUDENTS,
        "endpoints": {
            "students": "/students",
            "health": "/health",
            "student_mastery": "/students/{name}/mastery"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "System is running"}

@app.get("/students")
async def get_students():
    return {"students": SAMPLE_STUDENTS}

@app.get("/students/{student_name}/mastery")
async def get_student_mastery(student_name: str):
    if student_name not in SAMPLE_MASTERY:
        raise HTTPException(status_code=404, detail="Student not found")
    
    mastery_data = SAMPLE_MASTERY[student_name]
    return {
        "student": student_name,
        "topic_mastery": [
            {"topic": "Counting", "mastery": mastery_data["Counting"]},
            {"topic": "Number Recognition", "mastery": mastery_data["Number Recognition"]}
        ],
        "overall_mastery": mastery_data["Overall"]
    }

# Vercel handler
handler = app
