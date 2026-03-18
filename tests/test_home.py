from fastapi.testclient import TestClient
from fastapi import status
from home_expense_tracker import rest_api_app
import logging

test_client = TestClient(rest_api_app) # This is for Rest API to know this a test client and not an actual one
logger = logging.getLogger(__name__)


def test_app_home():
    response = test_client.get("/home")
    assert response.status_code == status.HTTP_200_OK
    logger.info(f"Response object {response}")
    assert response.json().get("message") == "Welcome to Home Expense Tracker"
