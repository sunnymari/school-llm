from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from db import Base

class ItemSchema(Base):
    __tablename__ = "item_schema"
    
    question = Column(Integer, primary_key=True, index=True)
    prompt_stub = Column(String, index=True)
    topic = Column(String, index=True)
    standard = Column(String, index=True)
    max_points = Column(Float)

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    student = Column(String, index=True)
    q1 = Column(Float)
    q2 = Column(Float)
    q3 = Column(Float)
    q4 = Column(Float)
    q5 = Column(Float)
    q6 = Column(Float)
    q7 = Column(Float)
    q8 = Column(Float)
    q9 = Column(Float)
    q10 = Column(Float)

class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    student = Column(String, index=True)
    topic = Column(String, index=True)
    total_points = Column(Float)
    max_points = Column(Float)
    mastery_percentage = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StandardMastery(Base):
    __tablename__ = "standard_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    student = Column(String, index=True)
    standard = Column(String, index=True)
    total_points = Column(Float)
    max_points = Column(Float)
    mastery_percentage = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
