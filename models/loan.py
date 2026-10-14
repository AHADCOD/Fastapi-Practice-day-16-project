from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.sql import func
from datetime import datetime, UTC
from .book import Book
from .member import Member

class Loan(Base):
    __tablename__ = "loans"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, primary_key=True)
    loan_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    return_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")

    book: Mapped["Book"] = relationship(back_populates="loans")
    member: Mapped["Member"] = relationship(back_populates="loans")