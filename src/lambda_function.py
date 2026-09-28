import json
import os

APP_VERSION = "1.0.0"


def lambda_handler(event, context):
    body = {
        "message": "Hello from the Kronos CI/CD pipeline",
        "version": APP_VERSION,
        "region": os.environ.get("AWS_REGION", "unknown"),
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }