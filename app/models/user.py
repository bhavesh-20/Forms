from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import text

from app.db import Base


class User(Base):
    __tablename__ = "users"
    # id column with server_default uuid4

    id = Column(
        UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()")
    )
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    forms = relationship("Form", cascade="all, delete", backref="users")
