import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)


'''
This tells SQLAlchemy where the database is and what kind it is.
The breakdown: 
    sqlite:/// tells it to use SQLite. 
    The ./expense.db part means "create a file named exactly expense.db in the exact same folder 
        where I am currently running this code
'''
SQL_ALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL","sqlite:///./expense_app.db")
if SQL_ALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQL_ALCHEMY_DATABASE_URL = SQL_ALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.debug(f'DB URL Set {SQL_ALCHEMY_DATABASE_URL}')

'''
The Engine is the core manager. 
It physically opens the connection to the database file and translates your Python code into actual SQL commands.
connect_args: This part is strictly for SQLite. 
              FastAPI handles multiple requests at the exact same time using different "threads." 
              By default, SQLite panics if multiple threads try to touch it. 
              Adding {'check_same_thread': False} tells SQLite, 
                "Relax, FastAPI knows what it's doing, let multiple requests talk to you.
'''
if SQL_ALCHEMY_DATABASE_URL.startswith("postgres"):
    db_engine = create_engine(SQL_ALCHEMY_DATABASE_URL, echo=True)
else:
    db_engine = create_engine(SQL_ALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}, echo=True)

logger.debug("DB Engine Created")

'''
This creates a Factory that will generate temporary database workspaces (Sessions) for you.
bind=db_engine: Tells the factory, "Whenever you create a new workspace, connect it to the Engine we just built"
autoflush=False: This is a safety feature. It tells SQLAlchemy, 
                    "Do not automatically push (flush) my changes to the database behind my back. 
                    Wait until I explicitly type .commit()"
'''
current_session = sessionmaker(autoflush=False, bind=db_engine)
logger.debug("DB Session Created")

'''
This creates a master "Registry" or "Catalog" class.
When you create your Python models (like class Expense(database_handle):), 
    inheriting from this base is how SQLAlchemy secretly knows that your Python class is supposed to be mapped 
    to a real database table. When you eventually run the command to create your tables, SQLAlchemy just looks 
    at this database_handle catalog, sees every class attached to it, and builds them all at once.
'''
DB_Handle = declarative_base()
logger.debug("DB Handle Created")
