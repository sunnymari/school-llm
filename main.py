from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
from openai import OpenAI

from app.db import SessionLocal, engine
from app.models import Base
from app.score import get_student_mastery, get_low_performing_areas, compute_aggregates
from app.rag import get_intervention_plan, search_interventions

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Assessment API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="web_ui"), name="static")
app.mount("/lti", StaticFiles(directory="lti_integration"), name="lti")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API
class AskRequest(BaseModel):
    student_name: str
    question: str
    threshold: Optional[float] = 70.0

class AskResponse(BaseModel):
    student_name: str
    mastery_summary: dict
    intervention_plan: str
    answer: str

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class SearchResponse(BaseModel):
    results: List[dict]

@app.get("/")
async def root():
    return {"message": "LLM Assessment API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/students")
async def list_students(db: Session = Depends(get_db)):
    """List all students in the database."""
    from app.models import Response
    students = db.query(Response.student).distinct().all()
    return {"students": [student[0] for student in students]}

@app.get("/students/{student_name}/mastery")
async def get_mastery(student_name: str, db: Session = Depends(get_db)):
    """Get mastery data for a specific student."""
    mastery_data = get_student_mastery(db, student_name)
    if not mastery_data["topic_mastery"]:
        raise HTTPException(status_code=404, detail="Student not found")
    return mastery_data

@app.get("/students/{student_name}/low-areas")
async def get_low_areas(student_name: str, threshold: float = 70.0, db: Session = Depends(get_db)):
    """Get low-performing areas for a specific student."""
    low_areas = get_low_performing_areas(db, student_name, threshold)
    if not low_areas["low_topics"] and not low_areas["low_standards"]:
        raise HTTPException(status_code=404, detail="Student not found or no low-performing areas")
    return low_areas

@app.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base for relevant content."""
    results = search_interventions(request.query, request.top_k)
    return SearchResponse(results=results)

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """Ask a question about a student and get an AI-powered response with intervention plan."""
    
    # Get student mastery data
    mastery_data = get_student_mastery(db, request.student_name)
    if not mastery_data["topic_mastery"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get low-performing areas
    low_areas = get_low_performing_areas(db, request.student_name, request.threshold)
    
    # Generate intervention plan using RAG
    intervention_plan = get_intervention_plan(low_areas, request.threshold)
    
    # Generate AI response using OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    client = OpenAI(api_key=openai_api_key)
    
    # Create context for the AI
    context = f"""
    Student: {request.student_name}
    
    Mastery Summary:
    - Topic Mastery: {mastery_data['topic_mastery']}
    - Standard Mastery: {mastery_data['standard_mastery']}
    
    Low-performing Areas (below {request.threshold}%):
    - Topics: {[area['topic'] for area in low_areas['low_topics']]}
    - Standards: {[area['standard'] for area in low_areas['low_standards']]}
    
    Suggested Intervention Plan:
    {intervention_plan}
    
    Question: {request.question}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational assessment expert. Provide helpful, actionable advice based on the student's performance data and intervention strategies."},
                {"role": "user", "content": context}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_answer = response.choices[0].message.content
        
    except Exception as e:
        ai_answer = f"AI response unavailable: {str(e)}"
    
    return AskResponse(
        student_name=request.student_name,
        mastery_summary=mastery_data,
        intervention_plan=intervention_plan,
        answer=ai_answer
    )

@app.post("/reload-data")
async def reload_data(db: Session = Depends(get_db)):
    """Reload assessment data and recompute mastery scores."""
    try:
        # Recompute aggregates
        compute_aggregates(db)
        return {"message": "Data reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload data: {str(e)}")

@app.get("/lti-config")
async def get_lti_config():
    """Serve LTI configuration file."""
    return FileResponse("lti_integration/lti_config.xml", media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
