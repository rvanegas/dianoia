"""not used"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from db.base import Base

class Conversation(Base):
    """not used"""
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True)
    # col1 = Column(String, nullable=False)
    # col2 = Column(String, unique=True, nullable=False)
    created_at = Column('created_at', DateTime, server_default=func.now())

# user = session.query(User).filter_by(name="Alice").first()
# print(user.email)
