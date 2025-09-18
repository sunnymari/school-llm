def handler(request):
    import json
    
    students = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    try:
        path = request.get("path", "/")
        
        if path == "/":
            response_data = {
                "message": "Math Assessment System is running!",
                "students": students
            }
        elif path == "/students":
            response_data = {"students": students}
        elif path == "/health":
            response_data = {"status": "healthy", "message": "System is running"}
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Endpoint not found"})
            }
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
