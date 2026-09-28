import json

from lambda_function import lambda_handler, APP_VERSION


def test_returns_200():
    response = lambda_handler({}, None)
    assert response["statusCode"] == 200


def test_body_contains_version():
    response = lambda_handler({}, None)
    body = json.loads(response["body"])
    assert body["version"] == APP_VERSION