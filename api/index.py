def handler(request):
    import json
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Math Assessment System is working!",
            "students": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "status": "success"
        })
    }
