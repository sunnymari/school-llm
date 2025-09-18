def handler(request):
    """Vercel serverless function handler"""
    import json
    
    # Sample data
    students = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    mastery_data = {
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
    
    # Get the path from the request
    path = request.get('path', '/')
    
    # Route handling
    if path == '/':
        response_data = {
            "message": "Math Assessment System is running!",
            "students": students,
            "endpoints": {
                "students": "/students",
                "health": "/health",
                "student_mastery": "/students/{name}/mastery"
            }
        }
    elif path == '/health':
        response_data = {"status": "healthy", "message": "System is running"}
    elif path == '/students':
        response_data = {"students": students}
    elif path.startswith('/students/') and path.endswith('/mastery'):
        # Extract student name from path like /students/Alice/mastery
        student_name = path.split('/')[2]
        if student_name in mastery_data:
            mastery = mastery_data[student_name]
            response_data = {
                "student": student_name,
                "topic_mastery": [
                    {"topic": "Counting", "mastery": mastery["Counting"]},
                    {"topic": "Number Recognition", "mastery": mastery["Number Recognition"]}
                ],
                "overall_mastery": mastery["Overall"]
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Student not found"})
            }
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Endpoint not found"})
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response_data)
    }
