from database import DB_Handle
from sqlalchemy import Column, Integer, Date, String, DECIMAL, CheckConstraint, ForeignKey


# It is suggested to use DECIMAL for money and Float for math related storage

class User(DB_Handle):
    __tablename__ = "User"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserName = Column(String(20), nullable=False, unique=True)
    HashedPassword = Column(String(20), nullable=False)
    FirstName = Column(String(20), nullable=False)
    EmailAddress = Column(String(30), nullable=True, default="test@email.com")

    __table_args__ = (
        CheckConstraint('length(UserName) > 3', 'check_username_length'),
        CheckConstraint('length(FirstName) > 3', 'check_firstname_length'),
     )


class Expense(DB_Handle):
    __tablename__ = "expense"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    PurchaseDate = Column(Date, nullable=False)
    Amount = Column(DECIMAL(10, 2), nullable=False)
    Store = Column(String(50), nullable=False, default="Walgreens")
    Card = Column(String(20), nullable=True)
    UserID = Column(Integer, ForeignKey("User.ID"), default=1)

    __table_args__ = (
        CheckConstraint('Amount > 0', name='check_amount_positive'),
    )
