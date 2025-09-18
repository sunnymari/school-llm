#!/usr/bin/env python3
import pandas as pd
from sqlalchemy.orm import Session
from app.db import Base, engine, SessionLocal
from app.models import ItemSchema, Response
from app.score import compute_aggregates

def main(schema_csv="./data/assessment_schema.csv", responses_csv="./data/responses.csv"):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    schema = pd.read_csv(schema_csv)
    db.query(ItemSchema).delete(); db.commit()
    db.bulk_insert_mappings(ItemSchema, [
        {"question": int(r["Question"]), "prompt_stub": str(r["PromptStub"]), "topic": str(r["Topic"]),
         "standard": str(r["Standard"]), "max_points": float(r["MaxPoints"])}
        for _, r in schema.iterrows()
    ]); db.commit()

    resp = pd.read_csv(responses_csv)
    db.query(Response).delete(); db.commit()
    def val(row, q): return float(row.get(f"Q{q}", 0))
    rows = []
    for _, r in resp.iterrows():
        rows.append({"student": str(r["Student"]),
                     "q1": val(r,1),"q2": val(r,2),"q3": val(r,3),"q4": val(r,4),"q5": val(r,5),
                     "q6": val(r,6),"q7": val(r,7),"q8": val(r,8),"q9": val(r,9),"q10": val(r,10)})
    db.bulk_insert_mappings(Response, rows); db.commit()

    compute_aggregates(db); db.close()
    print("Loaded schema and responses, computed aggregates.")

if __name__ == "__main__":
    main()
