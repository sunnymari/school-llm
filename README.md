# LLM Assessment Starter Project

A ready-to-run starter project that provides both a table & scoring pipeline (Question → Topic/Standard → Mastery) and a minimal LLM (RAG) service that reads mastery tables and returns actionable intervention plans.

## What's Inside

- `data/assessment_schema.csv` – maps each question to Topic & Standard
- `data/responses.csv` – sample student scores (Q1..Q10)
- `data/interventions.md` – educational intervention strategies
- `app/score.py` – computes ByTopic / ByStandard mastery
- `app/main.py` – FastAPI /ask endpoint (LLM + RAG)
- `app/rag.py` – builds & queries a small FAISS vector index over data/*.md
- `scripts/load_sample_data.py` – loads CSVs → SQLite and computes aggregates
- `scripts/build_index.py` – builds the vector index from data/interventions.md
- `requirements.txt`, `env.example`, `README.md`

## Features

- **Assessment Pipeline**: Automatically computes mastery scores by topic and standard
- **RAG-powered Interventions**: Uses vector search to find relevant teaching strategies
- **AI-powered Q&A**: Ask questions about student performance and get intelligent responses
- **REST API**: Clean FastAPI endpoints for integration with other systems
- **Multiple Interfaces**: Choose from Streamlit dashboard, Google Sheets integration, or LTI Canvas sidebar
- **CSV Upload/Download**: Easy data import and mastery results export
- **Real-time Sync**: Google Sheets integration for collaborative data entry

## Setup Instructions

### Quick Start (All Interfaces)

```bash
# 1. Setup environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure OpenAI API key
cp env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Load data and build index
python scripts/load_sample_data.py
python scripts/build_index.py

# 4. Launch everything
python launch_all.py
```

This will start all interfaces:
- **Streamlit Dashboard**: http://localhost:8501
- **Google Sheets Integration**: http://localhost:8502  
- **LTI Canvas Integration**: http://localhost:8503
- **API Documentation**: http://localhost:8000/docs

### Individual Interface Setup

#### Streamlit Dashboard
```bash
# Launch main dashboard
streamlit run streamlit_app/app.py --server.port 8501
```

#### Google Sheets Integration
```bash
# Launch Sheets integration
streamlit run web_ui/google_sheets_integration.py --server.port 8502
```

#### LTI Canvas Integration
```bash
# Launch LTI app
streamlit run lti_integration/lti_app.py --server.port 8503
```

#### API Only
```bash
# Launch just the API
uvicorn app.main:app --reload --port 8000
```

## Interface Options

### 🎯 Streamlit Dashboard (Recommended)
- **Best for**: Teachers and administrators
- **Features**: CSV upload/download, student analysis, AI Q&A
- **URL**: http://localhost:8501
- **Use cases**: 
  - Upload student response data
  - Analyze mastery scores
  - Get AI-powered insights
  - Download mastery reports

### 📊 Google Sheets Integration
- **Best for**: Collaborative teams, non-technical users
- **Features**: Real-time sync, shared editing, templates
- **URL**: http://localhost:8502
- **Use cases**:
  - Collaborative data entry
  - Sharing with colleagues
  - Integration with existing workflows
  - Template-based data collection

### 🎓 LTI Canvas Integration
- **Best for**: Students, embedded in LMS
- **Features**: Student-specific dashboard, progress tracking
- **URL**: http://localhost:8503
- **Use cases**:
  - Student self-assessment
  - Progress monitoring
  - Personalized learning guidance
  - LMS integration

### 🔧 API Documentation
- **Best for**: Developers, custom integrations
- **Features**: REST API, OpenAPI docs, testing interface
- **URL**: http://localhost:8000/docs
- **Use cases**:
  - Custom applications
  - Third-party integrations
  - Automated workflows
  - Data analysis scripts

## API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /students` - List all students
- `GET /students/{student_name}/mastery` - Get mastery data for a student
- `GET /students/{student_name}/low-areas` - Get low-performing areas
- `POST /ask` - Ask questions about student performance (main feature)

### Example Usage

#### Get all students:
```bash
curl http://localhost:8000/students
```

#### Get mastery data for Alice:
```bash
curl http://localhost:8000/students/Alice/mastery
```

#### Ask a question about a student:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Alice",
    "question": "What areas should Alice focus on improving?",
    "threshold": 70.0
  }'
```

#### Search intervention strategies:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "algebra linear equations",
    "top_k": 3
  }'
```

## Data Structure

### Assessment Schema
Each question is mapped to:
- **Topic**: Broad subject area (e.g., "Algebra", "Biology")
- **Standard**: Specific learning standard (e.g., "Linear Equations", "Plant Biology")
- **Max Points**: Maximum possible score

### Student Responses
Student scores are stored as Q1-Q10 with corresponding point values.

### Mastery Computation
The system automatically computes:
- **Topic Mastery**: Average performance across all questions in a topic
- **Standard Mastery**: Average performance across all questions for a specific standard

## RAG (Retrieval-Augmented Generation)

The system uses:
- **FAISS Vector Index**: For fast similarity search over intervention strategies
- **Sentence Transformers**: For embedding text into vector space
- **OpenAI GPT**: For generating intelligent responses based on retrieved context

## Customization

### Adding New Questions
1. Update `data/assessment_schema.csv` with new questions
2. Update `data/responses.csv` with student responses
3. Run `python scripts/load_sample_data.py` to recompute mastery

### Adding New Intervention Strategies
1. Add content to `data/interventions.md`
2. Run `python scripts/build_index.py` to rebuild the vector index

### Modifying the AI Model
Edit `app/main.py` to change the OpenAI model or parameters in the `/ask` endpoint.

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Make sure you've added your API key to the `.env` file
2. **Vector Index Not Found**: Run `python scripts/build_index.py` to create the index
3. **Database Errors**: Delete `assessment.db` and run `python scripts/load_sample_data.py` again

### Dependencies

If you encounter dependency issues:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## Next Steps

- Add more sophisticated assessment types (multiple choice, essay, etc.)
- Integrate with learning management systems
- Add student progress tracking over time
- Implement more advanced RAG techniques (hybrid search, re-ranking)
- Add authentication and user management
- Create a web UI for teachers and administrators

## License

This project is provided as-is for educational and development purposes.
