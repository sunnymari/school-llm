from sqlalchemy.orm import Session
from app.models import ItemSchema, Response, TopicMastery, StandardMastery

def compute_aggregates(db: Session):
    """Compute mastery scores by topic and standard for all students."""
    
    # Clear existing mastery records
    db.query(TopicMastery).delete()
    db.query(StandardMastery).delete()
    db.commit()
    
    # Get all students
    students = db.query(Response.student).distinct().all()
    
    for (student,) in students:
        # Get student's responses
        response = db.query(Response).filter(Response.student == student).first()
        if not response:
            continue
            
        # Create a mapping of question to score
        question_scores = {
            1: response.q1, 2: response.q2, 3: response.q3, 4: response.q4, 5: response.q5,
            6: response.q6, 7: response.q7, 8: response.q8, 9: response.q9, 10: response.q10
        }
        
        # Compute topic mastery
        topic_totals = {}
        for question, score in question_scores.items():
            schema = db.query(ItemSchema).filter(ItemSchema.question == question).first()
            if schema:
                topic = schema.topic
                if topic not in topic_totals:
                    topic_totals[topic] = {"total": 0, "max": 0}
                topic_totals[topic]["total"] += score
                topic_totals[topic]["max"] += schema.max_points
        
        # Save topic mastery
        for topic, totals in topic_totals.items():
            mastery_percentage = (totals["total"] / totals["max"]) * 100 if totals["max"] > 0 else 0
            topic_mastery = TopicMastery(
                student=student,
                topic=topic,
                total_points=totals["total"],
                max_points=totals["max"],
                mastery_percentage=mastery_percentage
            )
            db.add(topic_mastery)
        
        # Compute standard mastery
        standard_totals = {}
        for question, score in question_scores.items():
            schema = db.query(ItemSchema).filter(ItemSchema.question == question).first()
            if schema:
                standard = schema.standard
                if standard not in standard_totals:
                    standard_totals[standard] = {"total": 0, "max": 0}
                standard_totals[standard]["total"] += score
                standard_totals[standard]["max"] += schema.max_points
        
        # Save standard mastery
        for standard, totals in standard_totals.items():
            mastery_percentage = (totals["total"] / totals["max"]) * 100 if totals["max"] > 0 else 0
            standard_mastery = StandardMastery(
                student=student,
                standard=standard,
                total_points=totals["total"],
                max_points=totals["max"],
                mastery_percentage=mastery_percentage
            )
            db.add(standard_mastery)
    
    db.commit()

def get_student_mastery(db: Session, student_name: str):
    """Get mastery data for a specific student."""
    topic_mastery = db.query(TopicMastery).filter(TopicMastery.student == student_name).all()
    standard_mastery = db.query(StandardMastery).filter(StandardMastery.student == student_name).all()
    
    return {
        "topic_mastery": [
            {
                "topic": tm.topic,
                "total_points": tm.total_points,
                "max_points": tm.max_points,
                "mastery_percentage": tm.mastery_percentage
            }
            for tm in topic_mastery
        ],
        "standard_mastery": [
            {
                "standard": sm.standard,
                "total_points": sm.total_points,
                "max_points": sm.max_points,
                "mastery_percentage": sm.mastery_percentage
            }
            for sm in standard_mastery
        ]
    }

def get_low_performing_areas(db: Session, student_name: str, threshold: float = 70.0):
    """Get areas where student is performing below threshold."""
    mastery_data = get_student_mastery(db, student_name)
    
    low_topics = [
        tm for tm in mastery_data["topic_mastery"] 
        if tm["mastery_percentage"] < threshold
    ]
    
    low_standards = [
        sm for sm in mastery_data["standard_mastery"] 
        if sm["mastery_percentage"] < threshold
    ]
    
    return {
        "low_topics": low_topics,
        "low_standards": low_standards
    }
