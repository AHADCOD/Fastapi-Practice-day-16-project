from fastapi import APIRouter, Depends, status, Query, Path
from schemas.books import BookIn, BookOut, Genre, BookUpdate
from services.book_services import create_book_service, delete_book_service, get_books_service, get_available_book_service, get_book_service, update_book_service
from core.dependencies import require_admin, PaginationParams, get_pagination_params
from typing import Annotated
BookRouter = APIRouter(prefix="/books", tags=["Books"])

@BookRouter.post("/", response_model=BookOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_book(book: BookIn):
    book_dict = book.model_dump()  # Convert Pydantic model to dictionary
    return create_book_service(book_dict)

@BookRouter.get("/", response_model=list[BookOut])
def get_books(
    genre: Genre | None = Query(None, description="Filter books by genre"),
    author: str | None = Query(None, description="Filter books by author"),
    available_only: bool | None = Query(None, description="Filter books by availability"), pagination_params: PaginationParams = Depends(get_pagination_params)):
    return get_books_service(genre, author, available_only, pagination_params)

@BookRouter.get("/available", response_model=list[BookOut])
def get_available_books(pagination_params: PaginationParams = Depends(get_pagination_params)):
    return get_available_book_service(pagination_params)

@BookRouter.get("/{book_id}", response_model=BookOut)
def get_book(book_id: Annotated[int, Path(description="The ID of the book to retrieve", gt=0)]):
    return get_book_service(book_id)

@BookRouter.patch("/{book_id}", response_model=BookOut, response_model_exclude_unset= True)
def update_book(book_id: Annotated[int, Path(description="The ID of the book to update", gt=0)], book: BookUpdate):
    book_dict = book.model_dump(exclude_unset=True)
    return update_book_service(book_id, book_dict)

@BookRouter.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_book(book_id: Annotated[int, Path(..., gt=0)]):
    return delete_book_service(book_id)