from core.exceptions import DuplicateISBNError, BookNotFoundError, BookHasActiveLoansError
from schemas.books import Genre
from core.utilities import validate_isbn10_strict, validate_isbn13_strict
from core.dependencies import PaginationParams, pagination
books = {}

def check_book(book_id: int):
    if book_id not in list(books.keys()):
        raise BookNotFoundError(message="Book not found.")
    return books[book_id]



def create_book_service(book: dict):

    id = max(list(books.keys()))+1 if books else 1
    for existing_book in books.values():
        if book["isbn"] == existing_book["isbn"]:
            raise DuplicateISBNError(message="Book with this ISBN already exists.")
    books[id] = book
    return {"id": id, **books[id]}

def get_books_service( genre: Genre | None,
    author: str | None,
    available_only: bool | None, pagination_params: PaginationParams):
    results = []
    for id, book in books.items():
        if genre and book["genre"] != genre:
            continue
        if author and book["author"] != author:
            continue
        if available_only and book["available_copies"] <= 0:
            continue
        if book["isbn"] not in list(result["isbn"] for result in results):
            results.append({"id": id, **book})
    return pagination(pagination_params.skip, pagination_params.limit, results)

def get_available_book_service(pagination_params: PaginationParams):
    results = []
    for id, book in books.items():
        if book["available_copies"] > 0:
            if book["isbn"] not in list(result["isbn"] for result in results):
                results.append({"id": id, **book})
    return pagination(pagination_params.skip, pagination_params.limit, results)


def get_book_service(book_id: int):
    book = check_book(book_id)
    return {"id": book_id, **book}

def update_book_service(book_id: int, book_update: dict):
    book = check_book(book_id)
    
    for key, value in book_update.items():
        if value is not None:
            book[key] = value
    books[book_id] = book
    return {"id": book_id, **book}

def delete_book_service(book_id: int):
    from .loan_services import loans
    book = check_book(book_id)
    for loan in loans.values():
        if loan["book_id"] == book_id and loan["status"] == "active":
            raise BookHasActiveLoansError(message="Cannot delete book with active loans.")
    del books[book_id]


