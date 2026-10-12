from fastapi import FastAPI, Depends
from core.exceptions import register_exception_handlers
from routers.book import BookRouter
from routers.member import MemberRouter
from routers.loan import LoanRouter


app = FastAPI(title="library Management System")

register_exception_handlers(app)
app.include_router(BookRouter)
app.include_router(MemberRouter)
app.include_router(LoanRouter)

@app.get("/")
def root():
    return {"message": "Welcome"}

