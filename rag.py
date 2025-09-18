import os
import pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import faiss
import markdown
from bs4 import BeautifulSoup
import re

# Simple text-based search instead of embeddings for now
INDEX_FILE = "vector_index.pkl"
EMBEDDINGS_FILE = "embeddings.pkl"

def extract_text_from_markdown(md_content: str) -> str:
    """Extract plain text from markdown content."""
    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

def build_index(data_dir: str = "./data"):
    """Build simple text-based index from markdown files in data directory."""
    data_path = Path(data_dir)
    
    # Find all markdown files
    md_files = list(data_path.glob("*.md"))
    
    if not md_files:
        print(f"No markdown files found in {data_dir}")
        return
    
    documents = []
    
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract text from markdown
        text = extract_text_from_markdown(content)
        
        # Split into chunks (simple approach - split by double newlines)
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        
        for i, chunk in enumerate(chunks):
            if len(chunk) > 50:  # Only include substantial chunks
                documents.append({
                    'content': chunk,
                    'source': str(md_file),
                    'chunk_id': i
                })
    
    if not documents:
        print("No valid document chunks found")
        return
    
    # Save documents (no vector index for now)
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(documents, f)
    
    print(f"Built index with {len(documents)} document chunks")

def load_index():
    """Load the documents."""
    if not os.path.exists(EMBEDDINGS_FILE):
        return None
    
    with open(EMBEDDINGS_FILE, 'rb') as f:
        documents = pickle.load(f)
    
    return documents

def search_interventions(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search for relevant interventions based on query using simple text matching."""
    documents = load_index()
    
    if documents is None:
        return []
    
    # Simple text-based search
    query_words = set(re.findall(r'\w+', query.lower()))
    
    scored_documents = []
    for doc in documents:
        content_words = set(re.findall(r'\w+', doc['content'].lower()))
        
        # Calculate simple word overlap score
        overlap = len(query_words.intersection(content_words))
        total_words = len(query_words.union(content_words))
        score = overlap / total_words if total_words > 0 else 0
        
        scored_documents.append((score, doc))
    
    # Sort by score and return top_k
    scored_documents.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, doc in scored_documents[:top_k]:
        if score > 0:  # Only include documents with some relevance
            results.append({
                'content': doc['content'],
                'source': doc['source'],
                'score': score
            })
    
    return results

def get_intervention_plan(student_data: Dict[str, Any], threshold: float = 70.0) -> str:
    """Generate an intervention plan based on student mastery data."""
    
    # Extract low-performing areas
    low_topics = [area['topic'] for area in student_data.get('low_topics', [])]
    low_standards = [area['standard'] for area in student_data.get('low_standards', [])]
    
    if not low_topics and not low_standards:
        return "Great job! This student is performing well across all areas and doesn't need specific interventions at this time."
    
    # Search for interventions for each low-performing area
    intervention_plan = []
    
    for topic in low_topics:
        interventions = search_interventions(f"{topic} intervention strategies", top_k=2)
        if interventions:
            intervention_plan.append(f"**{topic}**:\n{interventions[0]['content']}\n")
    
    for standard in low_standards:
        interventions = search_interventions(f"{standard} teaching strategies", top_k=2)
        if interventions:
            intervention_plan.append(f"**{standard}**:\n{interventions[0]['content']}\n")
    
    if intervention_plan:
        return "\n".join(intervention_plan)
    else:
        return f"Focus on reviewing and practicing concepts in: {', '.join(low_topics + low_standards)}"
