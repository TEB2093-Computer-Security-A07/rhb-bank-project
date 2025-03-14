from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import datetime

Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customers'

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    account_number = Column(String)
    balance = Column(String)

    users = relationship("User", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Store encrypted password
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))

    customer = relationship("Customer", back_populates="users")


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class Transaction(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    transaction_type = Column(Enum(TransactionType))
    amount = Column(Float)
    recipient_account = Column(String, nullable=True)  # For transfers
    timestamp = Column(DateTime, default=datetime.datetime.now)

    customer = relationship("Customer", back_populates="transactions")
