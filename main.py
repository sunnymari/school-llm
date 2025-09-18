from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json

app = FastAPI(title="Math Assessment System", version="1.0.0")

# Sample data for demonstration
SAMPLE_STUDENTS = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", 
    "Frank", "Grace", "Henry", "Ivy", "Jack"
]

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

# Pydantic models
class AskRequest(BaseModel):
    student_name: str
    question: str
    threshold: Optional[float] = 70.0

class AskResponse(BaseModel):
    student_name: str
    mastery_summary: dict
    intervention_plan: str
    answer: str

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Math Assessment System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                padding: 3rem;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 600px;
                width: 90%;
            }
            
            h1 {
                color: #333;
                margin-bottom: 1rem;
                font-size: 2.5rem;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .feature {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            
            .feature h3 {
                color: #333;
                margin-bottom: 0.5rem;
            }
            
            .feature p {
                color: #666;
                font-size: 0.9rem;
            }
            
            .buttons {
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
                margin-top: 2rem;
            }
            
            .btn {
                background: #667eea;
                color: white;
                padding: 1rem 2rem;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s ease;
                display: inline-block;
            }
            
            .btn:hover {
                background: #5a6fd8;
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .btn-secondary {
                background: #6c757d;
            }
            
            .btn-secondary:hover {
                background: #5a6268;
            }
            
            .status {
                margin-top: 2rem;
                padding: 1rem;
                background: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 10px;
                color: #155724;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 2rem;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .buttons {
                    flex-direction: column;
                    align-items: center;
                }
                
                .btn {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧮 Math Assessment System</h1>
            <p class="subtitle">AI-powered insights for counting skills evaluation</p>
            
            <div class="features">
                <div class="feature">
                    <h3>🤖 AI Analysis</h3>
                    <p>Get intelligent insights and personalized recommendations for each student's performance</p>
                </div>
                <div class="feature">
                    <h3>📊 Real-time Analytics</h3>
                    <p>Track student progress with comprehensive mastery tracking and performance metrics</p>
                </div>
                <div class="feature">
                    <h3>🎯 Intervention Plans</h3>
                    <p>Receive targeted intervention strategies to help students improve their counting skills</p>
                </div>
            </div>
            
            <div class="buttons">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/students" class="btn btn-secondary">👥 View Students</a>
            </div>
            
            <div class="status">
                ✅ System is running and ready to analyze student performance!
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Math Assessment System is running"}

@app.get("/students")
async def list_students():
    """List all students in the system."""
    return {"students": SAMPLE_STUDENTS}

@app.get("/students/{student_name}/mastery")
async def get_mastery(student_name: str):
    """Get mastery data for a specific student."""
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

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a question about a student and get an AI-powered response."""
    
    if request.student_name not in SAMPLE_MASTERY:
        raise HTTPException(status_code=404, detail="Student not found")
    
    mastery_data = SAMPLE_MASTERY[request.student_name]
    
    # Generate intervention plan based on performance
    intervention_plan = generate_intervention_plan(mastery_data, request.threshold)
    
    # Generate AI response
    ai_answer = generate_ai_response(request.student_name, mastery_data, request.question, intervention_plan)
    
    return AskResponse(
        student_name=request.student_name,
        mastery_summary={
            "topic_mastery": [
                {"topic": "Counting", "mastery": mastery_data["Counting"]},
                {"topic": "Number Recognition", "mastery": mastery_data["Number Recognition"]}
            ],
            "overall_mastery": mastery_data["Overall"]
        },
        intervention_plan=intervention_plan,
        answer=ai_answer
    )

def generate_intervention_plan(mastery_data: dict, threshold: float) -> str:
    """Generate intervention plan based on student performance."""
    low_areas = []
    
    if mastery_data["Counting"] < threshold:
        low_areas.append("Counting")
    if mastery_data["Number Recognition"] < threshold:
        low_areas.append("Number Recognition")
    
    if not low_areas:
        return f"🎉 {request.student_name} is performing well above the {threshold}% threshold! Continue with current teaching strategies and consider enrichment activities."
    
    plan = f"📋 Intervention Plan for {request.student_name}:\n\n"
    plan += f"Areas needing attention (below {threshold}%): {', '.join(low_areas)}\n\n"
    
    if "Counting" in low_areas:
        plan += "🔢 Counting Interventions:\n"
        plan += "• Use manipulatives (blocks, counters) for hands-on practice\n"
        plan += "• Practice counting sequences (1-10, 1-20)\n"
        plan += "• Play counting games and songs\n"
        plan += "• One-on-one counting practice sessions\n\n"
    
    if "Number Recognition" in low_areas:
        plan += "🔤 Number Recognition Interventions:\n"
        plan += "• Flashcard practice with number symbols\n"
        plan += "• Number tracing and writing activities\n"
        plan += "• Number matching games\n"
        plan += "• Visual number charts and displays\n\n"
    
    plan += "📈 Progress Monitoring:\n"
    plan += "• Weekly assessment check-ins\n"
    plan += "• Document progress in learning journal\n"
    plan += "• Adjust interventions based on response\n"
    
    return plan

def generate_ai_response(student_name: str, mastery_data: dict, question: str, intervention_plan: str) -> str:
    """Generate AI response based on student data."""
    
    # Simple AI response without OpenAI API for demo
    overall_score = mastery_data["Overall"]
    
    if overall_score >= 90:
        performance_level = "excellent"
        encouragement = "outstanding work"
    elif overall_score >= 80:
        performance_level = "good"
        encouragement = "solid progress"
    elif overall_score >= 70:
        performance_level = "developing"
        encouragement = "steady improvement"
    else:
        performance_level = "needs support"
        encouragement = "targeted intervention"
    
    response = f"Based on {student_name}'s current performance data:\n\n"
    response += f"📊 Performance Summary: {student_name} shows {encouragement} with an overall mastery of {overall_score}%.\n\n"
    response += f"🎯 Current Status: {performance_level.title()} performance level\n\n"
    response += f"💡 Response to your question: {question}\n\n"
    
    if "counting" in question.lower():
        response += f"Counting Skills: {mastery_data['Counting']}% mastery. "
        if mastery_data['Counting'] >= 80:
            response += "Strong counting abilities demonstrated."
        else:
            response += "Additional counting practice recommended."
    
    if "number" in question.lower() or "recognition" in question.lower():
        response += f"Number Recognition: {mastery_data['Number Recognition']}% mastery. "
        if mastery_data['Number Recognition'] >= 80:
            response += "Good number recognition skills."
        else:
            response += "Number recognition needs reinforcement."
    
    response += f"\n\n{intervention_plan}"
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)