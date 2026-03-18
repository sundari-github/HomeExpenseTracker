import datetime
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import Annotated
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from database import current_session
from models import User
from jose import JWTError, jwt

JWT_SECRET = "9dcd37c10a59507d0ee7abcdf8ee609d4ab59ee587685bf50af07fb39383a947"  # openssl rand -hex 32|16
JWT_ALGO = "HS256"


def get_db_session():
    db_session = current_session()
    try:
        yield db_session
    finally:
        db_session.close()


auth_end_point = APIRouter(prefix="/auth", tags=["Authorization Management"])
logger = logging.getLogger(__name__)
db_dependency = Annotated[Session, Depends(get_db_session)]
bcrypt_context = CryptContext(schemes=['bcrypt'])
oath2_bearer = OAuth2PasswordBearer(tokenUrl='auth/getToken')

'''
JWT tokens are flexible and can be customized based on your needs. Here's what you should know:
Standard Claims (Optional but Recommended):
    sub - Subject (user identifier)
    exp - Expiration time
    iat - Issued at
    iss - Issuer
    aud - Audience
These are defined in JWT specifications and are widely recognized, 
'''


def create_access_token(userid: str, username: str, expires: timedelta):
    exp = datetime.datetime.now(datetime.timezone.utc) + expires
    logger.debug(f'JWT Payload inputs {userid} {username} {expires}')
    jwt_payload = {"userid": userid, "username": username, "exp": exp}
    return jwt.encode(claims=jwt_payload, algorithm=JWT_ALGO, key=JWT_SECRET)
    

def get_current_user(token: Annotated[str, Depends(oath2_bearer)]):
    logger.debug("Inside get_current_user")
    try:
        jwt_payload = jwt.decode(token=token, key=JWT_SECRET, algorithms=JWT_ALGO)
        userid = jwt_payload.get("userid")
        username = jwt_payload.get("username")
        if userid is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return {"ID": userid, "UserName": username}
    except JWTError as e:
        logger.error(f"JWT decoding error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


'''
Because Depends() is empty, FastAPI automatically looks to the left, 
sees OAuth2PasswordRequestForm, and translates your code into this behind the scenes:
    form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)]
It is simply a shortcut to save you from typing the exact same long class name twice

When FastAPI sees this dependency, it does the following:
    It instantiates the OAuth2PasswordRequestForm class.
    It looks at the incoming HTTP request.
    It extracts the username and password from the request and populates the class.
    It injects that fully populated object into your form_data variable so you can use it in your function
    
Without Depends(): FastAPI assumes every single parameter in your function is supposed to come from a standard 
                   JSON body. It will reject the request because the client isn't sending JSON.

With Depends(): It triggers FastAPI's Dependency Injection system. The OAuth2PasswordRequestForm class is specifically 
                written to tell FastAPI: "Do not look for JSON! Use python-multipart to parse this as 
                application/x-www-form-urlencoded Form Data!"

Without the empty Depends(), FastAPI never triggers the form-parsing logic, and your authentication endpoint will crash

we can set a include_in_schema=False parameter to the post below to hide this from the swagger docs. But this would
prevent the Green "Authorize" padlock that appears on Swagger that helps you enter the userid and password for obtaining
the token.     
'''


@auth_end_point.post("/getToken", summary="Returns the token for authorization", status_code=status.HTTP_200_OK)
async def get_token(db_session: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    logger.debug("Inside Authenticate user method")
    db_rows = db_session.query(User).filter(form_data.username == User.UserName).first()
    if not db_rows:
        raise HTTPException(status_code=401, detail="Unauthorized access. Invalid User")
    logger.debug(f"UserName valid {db_rows.ID} {db_rows.UserName}")
    is_passwd_valid = bcrypt_context.verify(form_data.password, db_rows.HashedPassword)
    if not is_passwd_valid:
        raise HTTPException(status_code=401, detail="Unauthorized access. Invalid Password")
    logger.debug(f"Password valid")
    token = create_access_token(db_rows.ID, db_rows.UserName, timedelta(minutes=20))

    return {"access_token": token, "token_type": "bearer"}
