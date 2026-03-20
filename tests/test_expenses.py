from decimal import Decimal
from fastapi import status
import pytest


@pytest.mark.parametrize("from_date,to_date,expected_status,expected_len",
                         [
                             ("2026-03-13", "2026-03-14", status.HTTP_200_OK, 2),  # both rows
                             ("2026-03-14", "2026-03-14", status.HTTP_200_OK, 1),  # single day
                             ("2026-03-14", "2026-03-15", status.HTTP_200_OK, 2),  # two days
                             ("2026-03-13", "2026-03-16", status.HTTP_200_OK, 4),  # multiple days
                             ("2026-03-17", "2026-03-18", status.HTTP_204_NO_CONTENT, 0),  # none
                             ("2026-03-14", "2026-03-13", status.HTTP_204_NO_CONTENT, 0)  # reversed range → none
                         ]
                         )
def test_01_get_expenses_by_date(client, seed_expenses, from_date, to_date, expected_status, expected_len):
    r = client.get(f"/expense/getExpensesByDate/{from_date}/{to_date}")
    assert r.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        data = r.json()
        assert isinstance(data, list) and len(data) == expected_len
    if expected_status == status.HTTP_204_NO_CONTENT:
        assert r.content == b''  # No content should be empty


@pytest.mark.parametrize("category_name, category_value, expected_status, expected_len",
                         [
                             ("Store", "Walgreens", status.HTTP_200_OK, 1),  # matches e1
                             ("Card", "Visa", status.HTTP_200_OK, 1),  # matches e2
                             ("Store", "NonExistentStore", status.HTTP_204_NO_CONTENT, 0),  # no match
                             ("InvalidCategory", "Value", status.HTTP_422_UNPROCESSABLE_CONTENT, 0)  # invalid category
                         ]
                         )
def test_02_get_expenses_by_category(client, seed_expenses, category_name, category_value, expected_status,
                                     expected_len):
    r = client.get(f"/expense/getExpenses?category_name={category_name}&category_value={category_value}")
    assert r.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        data = r.json()
        assert isinstance(data, list) and len(data) == expected_len
    if expected_status == status.HTTP_204_NO_CONTENT:
        assert r.content == b''  # No content should be empty


def test_03_update_expense(client, seed_expenses):
    # Get an existing expense to update
    r = client.get("/expense/getAllExpenses")
    assert r.status_code == status.HTTP_200_OK
    expenses = r.json()
    assert len(expenses) > 0
    expense_id = expenses[0]['ID']
    
    # Update the expense
    expenses[0]['Amount'] = 50.55
    expenses[0]['Card'] = "Mastercard"
    r = client.put(f"/expense/updateExpense", json=expenses[0])
    assert r.status_code == status.HTTP_200_OK
    assert r.json() == {"message": "Successfully updated the expenses matching the condition"}

    # Verify the update
    r = client.get(f'/expense/getExpenses?category_name=Card&category_value=Mastercard')
    assert r.status_code == status.HTTP_200_OK
    assert isinstance(r.json(), list) and len(r.json()) == 2  # e3 and the updated e1
    updated_expense = next((e for e in r.json() if e['ID'] == expense_id), None)
    assert updated_expense is not None
    assert Decimal(str(updated_expense['Amount'])) == Decimal('50.55')
    assert updated_expense['Card'] == "Mastercard"


def test_04_delete_expense(client, seed_expenses):
    # Get an existing expense to delete
    r = client.get("/expense/getAllExpenses")
    assert r.status_code == status.HTTP_200_OK
    expenses = r.json()
    assert len(expenses) > 0
    expense_id = expenses[0]['ID']

    # Delete the expense
    r = client.delete(f"/expense/deleteExpense/{expenses[0]['Store']}/{expenses[0]['PurchaseDate']}")
    assert r.status_code == status.HTTP_200_OK
    assert r.json() == {"message": "Successfully deleted the expenses matching the condition"}

    # Verify the deletion
    r = client.get(f"/expense/getExpensesByDate/2026-03-13/2026-03-14")
    assert r.status_code == status.HTTP_200_OK
    deleted_expense = next((e for e in r.json() if e['ID'] == expense_id), None)
    assert deleted_expense is None
