from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, BaseModel
import logging
from models import User
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from database import current_session
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from starlette import status
from .auth import get_current_user


def get_db_session():
    db_session = current_session()
    try:
        yield db_session
    finally:
        db_session.close()


users_endpoint = APIRouter(prefix="/users", tags=["User Management"])
logger = logging.getLogger(__name__)
db_dependency = Annotated[Session, Depends(get_db_session)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'])  # Hashing algo bcrypt is going to be used


class UserInput(BaseModel):
    UserName: str = Field(min_length=3, description="Unique User name for identification")
    Password: str = Field(min_length=8, description="Password for the user")
    FirstName: str = Field(min_length=3, description="First Name of the user")
    EmailAddress: Optional[str] = Field(default=None, description="Email Address of the user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "UserName": "sund",
                "Password": "******",
                "FirstName": "Sundari",
                "EmailAddress": "test@gmail.com"
            }
        }
    }


@users_endpoint.post("/createUser", summary="Creating a new user", status_code=status.HTTP_201_CREATED)
async def create_user(db_rows: db_dependency, user_input: UserInput):
    logger.debug(f"Inside Create User {user_input}")
    try:
        db_row_to_be_added = User(UserName=user_input.UserName,
                                  HashedPassword=bcrypt_context.hash(user_input.Password),
                                  FirstName=user_input.FirstName,
                                  EmailAddress=user_input.EmailAddress)
        db_rows.add(db_row_to_be_added)
        db_rows.commit()
        return {"message": "Successfully added a user to the database"}
    except SQLAlchemyError as e:
        db_rows.rollback()
        if hasattr(e, 'orig') and e.orig:
            error_desc = str(e.orig)
        else:
            error_desc = str(e)
        logger.error(f'Error in DB {error_desc}')
        raise HTTPException(status_code=400, detail=f"Error in adding user to the database: {error_desc}")


@users_endpoint.get("/getUserDetails", summary="Get details of user", status_code=status.HTTP_200_OK)
async def get_user_details(user_info: user_dependency, db_row: db_dependency):
    logger.debug("Inside get_user")
    user_row_in_db = db_row.query(User).filter(User.ID == int(user_info.get("ID"))).first()
    if not user_row_in_db:
        raise HTTPException(status_code=204, detail="No rows found in DB")
    return user_row_in_db


@users_endpoint.post("/changeUserPassword", summary="Change Password for user",
                     status_code=status.HTTP_200_OK)
async def change_user_password(user_info: user_dependency, db_row: db_dependency,
                          old_password: str = Query(..., min_length=8, description="Old password value"),
                          new_password: str = Query(..., min_length=8, description="New Password value")):
    logger.debug("Inside change password")
    user_row_db = db_row.query(User).filter(User.ID == int(user_info.get("ID"))).first()
    if not user_row_db:
        raise HTTPException(status_code=401, detail="Invalid User")
    hashed_old_passwd = bcrypt_context.hash(old_password)
    logger.debug(f'old hash value {hashed_old_passwd}')
    logger.debug(f'value in DB {user_row_db.HashedPassword}')
    is_password_matching = bcrypt_context.verify(old_password, user_row_db.HashedPassword)
    if not is_password_matching:
        raise HTTPException(status_code=401, detail="Old Password does not match")
    user_row_db.HashedPassword = bcrypt_context.hash(new_password)
    db_row.commit()
    return {"message": "Password changed successfully"}


@users_endpoint.put("/modifyUserDetails", summary="Modifying the first name or email address of a user",
                    status_code=status.HTTP_200_OK)
async def modify_user_details(user_info: user_dependency, db_row: db_dependency,
                              first_name: Optional[str] = Query(default=None,
                                                                description="First name value to be updated with"),
                              email_addr: Optional[str] = Query(default=None,
                                                                description="Email address to be updated with")):
    logger.debug("Inside Modify user details")
    user_row_db = db_row.query(User).filter(int(user_info.get("ID")) == User.ID).first()
    if user_row_db is None:
        raise HTTPException(status_code=401, detail="Invalid user id")
    if first_name is not None:
        logger.debug(f'Updating first name {first_name}')
        user_row_db.FirstName = first_name
    else:
        logger.debug("No updates to first name")
    if email_addr is not None:
        logger.debug(f'Updating Email Addr {email_addr}')
        user_row_db.EmailAddress = email_addr
    else:
        logger.debug("No updates to email address")
    db_row.commit()
    return {"message": "User details updated successfully"}