# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import DB_Handle
from home_expense_tracker import rest_api_app
from router.expenses import get_db_session as expense_get_db_session
from router.users import get_db_session as users_get_db_session
from router.auth import get_current_user
from fastapi import status

from models import Expense, User

TEST_DB_URL = "sqlite:///./test_expense_app.db"
# print("CWD:", os.getcwd())
# print("Resolved test DB:", os.path.abspath("test_expense_app.db"))
test_db_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, echo=False)
TestingSessionLocal = sessionmaker(autoflush=False, bind=test_db_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Ensure clean slate: drop and remove any stale DB before starting
    test_db_engine.dispose()
    if os.path.exists("test_expense_app.db"):
        try:
            os.remove("test_expense_app.db")
        except PermissionError:
            pass
    
    DB_Handle.metadata.create_all(bind=test_db_engine)
    try:
        yield
    finally:
        DB_Handle.metadata.drop_all(bind=test_db_engine)
        test_db_engine.dispose()
        # Optional: remove the SQLite file for a fully clean slate
        if os.path.exists("test_expense_app.db"):
            try:
                os.remove("test_expense_app.db")
            except PermissionError:
                pass


@pytest.fixture(scope="session")
def override_get_db_session():
    def get_test_db_session():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()
    return get_test_db_session


@pytest.fixture(scope="session")
def override_get_current_user():
    # Ensure tests operate as user ID 1
    return lambda: {"ID": 1, "UserName": "sund", "FirstName": "Sundari"}


@pytest.fixture(scope="session")
def app(override_get_db_session, override_get_current_user):
    # Apply overrides once for the whole session
    rest_api_app.dependency_overrides[expense_get_db_session] = override_get_db_session
    rest_api_app.dependency_overrides[users_get_db_session] = override_get_db_session
    rest_api_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield rest_api_app
    finally:
        rest_api_app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session")
def seed_user(client, setup_database):
    # Clean users and expenses once for the session
    with TestingSessionLocal() as s:
        s.query(Expense).delete()
        s.query(User).delete()
        s.commit()

    payload = {
        "UserName": "sund",
        "Password": "testing123?",  # >=8 chars for validation
        "FirstName": "Sundari",
        "EmailAddress": "test@example.com",
    }
    r = client.post("/users/createUser", json=payload)
    # Idempotent: allow 201 (created) or 400 (already exists)
    assert r.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST)
    return payload


@pytest.fixture(scope="session")
def seed_expenses(client, seed_user):
    # Clean only expenses (preserve the seeded user)
    with TestingSessionLocal() as s:
        s.query(Expense).delete()
        s.commit()

    e1 = {"PurchaseDate": "2026-03-13", "Amount": 23.44, "Store": "Walgreens", "Card": "Amex"}
    e2 = {"PurchaseDate": "2026-03-14", "Amount": 99.99, "Store": "Target", "Card": "Visa"}
    e3 = {"PurchaseDate": "2026-03-15", "Amount": 67.09, "Store": "Walmart", "Card": "Mastercard"}
    e4 = {"PurchaseDate": "2026-03-16", "Amount": 18.35, "Store": "Kings", "Card": "Discover"}

    r1 = client.post("/expense/addExpense", json=e1)
    assert r1.status_code == status.HTTP_201_CREATED
    assert r1.json() == {"message": "Successfully added an expenses into the database"}

    r2 = client.post("/expense/addExpense", json=e2)
    assert r2.status_code == status.HTTP_201_CREATED
    assert r2.json() == {"message": "Successfully added an expenses into the database"}

    r3 = client.post("/expense/addExpense", json=e3)
    assert r3.status_code == status.HTTP_201_CREATED
    assert r3.json() == {"message": "Successfully added an expenses into the database"}

    r4 = client.post("/expense/addExpense", json=e4)
    assert r4.status_code == status.HTTP_201_CREATED
    assert r4.json() == {"message": "Successfully added an expenses into the database"}

    # Verify count via API
    r = client.get("/expense/getAllExpenses")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert isinstance(data, list) and len(data) == 4
    return [e1, e2]
