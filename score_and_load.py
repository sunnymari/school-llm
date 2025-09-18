#!/usr/bin/env python3
from sqlalchemy.orm import Session
from app.db import Base, engine, SessionLocal
from app.score import compute_aggregates

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    compute_aggregates(db)
    db.close()
    print("Recomputed aggregates.")
