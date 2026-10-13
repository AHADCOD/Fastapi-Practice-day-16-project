from fastapi import FastAPI, Depends
from core.exceptions import register_exception_handlers
from routers.book import BookRouter
from routers.member import MemberRouter
from routers.loan import LoanRouter
from routers.publisher import PublisherRouter
from models.book import Book
from models.publisher import Publisher
from core.database import Base, engine


app = FastAPI(title="library Management System")

Base.metadata.create_all(bind=engine)
register_exception_handlers(app)
app.include_router(BookRouter)
app.include_router(MemberRouter)
app.include_router(LoanRouter)
app.include_router(PublisherRouter)


@app.get("/")
def root():
    return {"message": "Welcome"}

