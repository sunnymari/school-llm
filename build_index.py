#!/usr/bin/env python3
from app.rag import build_index
if __name__ == "__main__":
    build_index("./data")
    print("Vector index built and saved.")
