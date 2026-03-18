import logging

from fastapi import APIRouter, Query, Path, HTTPException, Depends
from datetime import date
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Literal, Annotated
from starlette import status
from models import Expense
from database import current_session
from sqlalchemy.orm import Session
from .auth import get_current_user

expenses_endpoint = APIRouter(prefix="/expense", tags=["Expense Management"])
logger = logging.getLogger(__name__)


def get_db_session():
    db_session = current_session()
    try:
        yield db_session
    finally:
        db_session.close()


'''
Dependency Injection system.

Depends(expense_rows_in_db): This tells FastAPI: 
                              "Before you even run this endpoint, pause and go run the expense_rows_in_db function." 
                              That function opens a fresh connection (session) to the database.

db_session: Session: This takes the open database connection that Depends just handed over, names it db_session, and 
             type-hints it as an SQLAlchemy Session so your IDE knows what methods are available.

Annotated[...]: This is just the modern Python 3.9+ way of combining a type hint (Session) 
                with FastAPI metadata (Depends). It keeps the code clean and strictly typed.
                An equivalent of Session db_session = get_db_session() 

This is passed as the first parameter to any API end-point function that needs to work with the database                
'''
db_dependency = Annotated[Session, Depends(get_db_session)]
user_dependency = Annotated[dict, Depends(get_current_user)]  # dict user_dependency = (dict) get_current_user()


class ExpenseApiInput(BaseModel):
    PurchaseDate: date = Field(description="Should be in YYYY-MM-DD format")
    Amount: Decimal = Field(gt=0, decimal_places=2,
                            description="Should be a positive number with maximum 2 decimal places")
    Store: str = Field(min_length=1, description="Should be a non empty string")
    Card: Literal["Amex", "Visa", "Mastercard", "Discover"]

    # noinspection PyNestedDecorators
    @field_validator('Store')
    @classmethod
    def check_store_not_empty_spaces(cls, value: str):
        if not value.strip():  # If the string is empty after removing spaces
            raise ValueError('Store name cannot be just blank spaces')
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "PurchaseDate": "2026-02-24",
                "Amount": 45.99,
                "Store": "Target",
                "Card": "Visa"
            }
        }
    }


# expense_details = [
#     ExpenseApiInput(ID=1, PurchaseDate="2026-01-01", Amount=20.34, Store="Walmart", Card="Amex"),
#     ExpenseApiInput(ID=2, PurchaseDate="2026-01-05", Amount=202.23, Store="Stop & Shop", Card="Visa"),
#     ExpenseApiInput(ID=3, PurchaseDate="2026-01-30", Amount=89.49, Store="Walgreens", Card="Mastercard"),
#     ExpenseApiInput(ID=4, PurchaseDate="2026-02-01", Amount=120.34, Store="Shop Rite", Card="Discover"),
#     ExpenseApiInput(ID=5, PurchaseDate="2026-02-14", Amount=50.74, Store="Costco", Card="Amex")
# ]

'''
It is always suggested to define methods with more generic path before the specific ones. 
That way, the generic call would go to the generic one and the specific call would go to the specific ones
Failing this, the generic call will be matched with the specific one with an incorrect param value resulting
    in failed execution status.
'''


@expenses_endpoint.get("/getAllExpenses", summary="Returns all the saved expenses", status_code=status.HTTP_200_OK)
async def get_all_expenses(user_info: user_dependency, db_rows: db_dependency):
    logger.debug("Get all expenses invoked")
    db_result = db_rows.query(Expense).filter(Expense.UserID == int(user_info["ID"])).all()
    # Usually no row found is not an exception scenario
    # if not db_result:
    #     raise HTTPException(status_code=204, detail="No rows found in DB")
    return db_result


@expenses_endpoint.get("/getExpensesByDate/{from_date}/{to_date}",
                       summary="Returns the list of expenses between the dates mentioned",
                       status_code=status.HTTP_200_OK)
async def get_expense_by_date(
        user_info: user_dependency,
        db_rows: db_dependency,
        from_date: date = Path(..., description="The starting date from which expenses need to be filtered"),
        to_date: date = Path(..., description="The ending date until which expenses need to be filtered")):
    logger.debug(f'From Date {from_date}')
    logger.debug(f'To Date {to_date}')
    '''
    to_be_returned_expenses = []
    for expense in expense_details:
        logger.debug(f'Expense Date {expense.PurchaseDate}')
        # expense_date_iso = date.fromisoformat(expense.Date)
        if from_date <= expense.PurchaseDate <= to_date:
            logger.debug("Adding expense to the returned value")
            to_be_returned_expenses.append(expense)
    if len(to_be_returned_expenses) == 0:
        raise HTTPException(status_code=204, detail="No expenses found between the dates")
    return to_be_returned_expenses
    '''
    matching_rows = db_rows.query(Expense).filter(Expense.UserID == int(user_info.get("ID")),
                                                  Expense.PurchaseDate.between(from_date, to_date)).all()
    if not matching_rows:
        raise HTTPException(status_code=204, detail="No expenses found between the dates")
    return matching_rows


@expenses_endpoint.get("/getExpenses",
                       summary="Returns the list of expenses based on the category in filter",
                       status_code=status.HTTP_200_OK)
async def get_expense_by_category(
        user_info: user_dependency,
        db_rows: db_dependency,
        category_name: str = Query(..., min_length=1, description="Can either be Store or Card"),
        category_value: str = Query(..., min_length=1, description="Value to be filtered for the category")):
    logger.debug(f'Category Name {category_name}\nCategory Value {category_value}')
    '''
    to_be_returned_expenses = []
    for expense in expense_details:
        if category_name.casefold() == "Store".casefold():
            category_value_in_expense = expense.Store
        elif category_name.casefold() == "Card".casefold():
            category_value_in_expense = expense.Card
        else:
            logger.error("Invalid Category Name")
            raise HTTPException(status_code=422, detail="Invalid category name in query parameter")
        if category_value_in_expense.casefold() == category_value.casefold():
            to_be_returned_expenses.append(expense)
    if len(to_be_returned_expenses) == 0:
        raise HTTPException(status_code=204, detail="No expenses match the category value filter")
    return to_be_returned_expenses
    '''
    if category_name.casefold() == "Store".casefold():
        matching_rows = db_rows.query(Expense).filter(Expense.UserID == int(user_info.get("ID")),
                                                      Expense.Store.ilike(category_value)).all()
    elif category_name.casefold() == "Card".casefold():
        matching_rows = db_rows.query(Expense).filter(Expense.UserID == int(user_info.get("ID")),
                                                      Expense.Card.ilike(category_value)).all()
    else:
        logger.error("Invalid Category Name")
        raise HTTPException(status_code=422, detail="Invalid category name in query parameter")

    if not matching_rows:
        raise HTTPException(status_code=204, detail="No expenses match the category value filter")
    return matching_rows


@expenses_endpoint.post("/addExpense",
                        summary="Adds an additional expense entry",
                        status_code=status.HTTP_201_CREATED)
async def add_expense(user_info: user_dependency, db_rows: db_dependency, expense_api_input: ExpenseApiInput):
    #  1. Convert the Pydantic object to a dictionary.
    #  mode='json' safely converts the 'date' object back into a "YYYY-MM-DD" string!
    #  expense_dict = expense.model_dump(mode='json')
    #  2. Append the new dictionary to your local list
    # logger.debug(f"Input Expense {expense}")
    # expense.ID = get_expense_id()
    # logger.debug(f'ID generated {expense.ID}')
    # expense_details.append(expense)
    logger.debug(f"Inside Add Expense {expense_api_input}")
    '''
      model_dump packages this into a standard python dictionary
      ** instructs python not to just pass the dictionary to the Expense data model object 
          Instead, map the columns in Expense Data Model to the keys in the dictionary and send me 
          the data to the Expense object  
          The column names must match exactly (and they are case-sensitive).
      '''
    db_row_to_be_added = Expense(**expense_api_input.model_dump(), UserID=user_info.get("ID"))
    db_rows.add(db_row_to_be_added)
    db_rows.commit()
    return {"message": "Successfully added an expenses into the database"}


# def get_expense_id():
#     max_id = 0
#     for expense in expense_details:
#         if expense.ID > max_id:
#             max_id = expense.ID
#     return max_id+1


@expenses_endpoint.put("/updateExpense",
                       summary="Updates the attributes of an expense for a given date at given store",
                       status_code=status.HTTP_200_OK)
async def update_expense(user_info: user_dependency, db_rows: db_dependency, input_expense: ExpenseApiInput):
    logger.debug(f'Input Expense {input_expense}')
    # for expense in expense_details:
    #     logger.debug(f'Expense in Loop {expense}')
    #     '''
    #     input_expense_dict = input_expense.model_dump(mode="json")
    #     if expense["Date"] == input_expense_dict["Date"] and expense["Store"] == input_expense_dict["Store"]:
    #         expense["Amount"] = input_expense_dict["Amount"]
    #         expense["Card"] = input_expense_dict["Card"]
    #         return
    #     '''
    #     if (input_expense.PurchaseDate == expense.PurchaseDate and
    #             input_expense.Store.casefold() == expense.Store.casefold()):
    #         expense.Amount = input_expense.Amount
    #         expense.Card = input_expense.Card
    #         return
    #     raise HTTPException(status_code=404, detail="No matching expense found for updates")
    matching_rows = db_rows.query(Expense).filter(Expense.UserID == int(user_info.get("ID")),
                                                  input_expense.PurchaseDate == Expense.PurchaseDate,
                                                  input_expense.Store == Expense.Store).all()
    if not matching_rows:
        raise HTTPException(status_code=404, detail="No matching expense found for updates")
    for expense in matching_rows:
        expense.Amount = input_expense.Amount
        expense.Card = input_expense.Card
        db_rows.add(expense)
        logger.debug(f"Expense updated {expense}")
    db_rows.commit()
    return {"message": "Successfully updated the expenses matching the condition"}


@expenses_endpoint.delete("/deleteExpense/{store_name}/{date_of_purchase}",
                          summary="Delete an expense record based on the store and the date of purchase",
                          status_code=status.HTTP_200_OK)
async def delete_expense(
        user_info: user_dependency,
        db_rows: db_dependency,
        store_name: str = Path(..., description="Store name identifying the purchase to be deleted"),
        date_of_purchase: date = Path(..., description="Date of purchase identifying the expense to be deleted")):
    # date_str_format = date_of_purchase.isoformat()
    # logger.debug(f'Store Name {store_name}\nDate Of Purchase {date_of_purchase}')
    # for expense in expense_details:
    #     if expense.Store.casefold() == store_name.casefold() and expense.PurchaseDate == date_of_purchase:
    #         expense_details.remove(expense)
    #         return
    # raise HTTPException(status_code=404, detail="No matching expense found for deletion")
    logger.debug("Inside delete expense")
    '''
    The below approach is better for performance, than looping the output of .all() and deleting one by one
    .all() approach: SQLAlchemy sends a SELECT query to the database.
                    The database sends the data back to Python.
                    Python uses your computer's memory to build full Expense objects for every single row.
                    loop through them one by one and tell SQLAlchemy to mark them for deletion.
                    .commit(), which sends multiple DELETE commands back to the database.
    '''
    deleted_row_count = db_rows.query(Expense).filter(Expense.UserID == int(user_info.get("ID")),
                                                      Expense.Store.ilike(store_name),
                                                      Expense.PurchaseDate == date_of_purchase).delete()
    db_rows.commit()
    if deleted_row_count == 0:
        raise HTTPException(status_code=404, detail="No matching expense found for deletion")
    return {"message": "Successfully deleted the expenses matching the condition"}
