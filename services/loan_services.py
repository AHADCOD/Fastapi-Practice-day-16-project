from datetime import datetime, timedelta, UTC, UTC
from schemas.loans import ReturnStatus
from schemas.books import BookOut
from schemas.members import MemberOut
from .book_services import check_book
from .member_services import check_member
from core.exceptions import BookUnavailableError, LoanNotFoundError, DuplicateLoanError, LoanLimitExceededError
from core.dependencies import PaginationParams, pagination

loans = {}

def check_loan(loan_id: int):
    if loan_id not in list(loans.keys()):
        raise LoanNotFoundError(message="Loan not found.")
    return loans[loan_id]

def get_member_and_book_details(loan: dict):
    member_id = loan["member_id"]
    book_id = loan["book_id"]
    member = check_member(member_id)
    book = check_book(book_id)
    return MemberOut(id=member_id, **member), BookOut(id=book_id, **book)


def create_loan_service(member_id: int, book_id: int):
    
    member = check_member(member_id)
    book = check_book(book_id)

    if book["available_copies"] <= 0:
        raise BookUnavailableError(message="Book is currently unavailable for loan.")

    for loan in loans.values():
        if loan["book_id"] == book_id and loan["member_id"] == member_id and loan["status"] == ReturnStatus.ACTICE:
            raise DuplicateLoanError(message="This member already has an active loan for this book.")


    member_loan_count = sum(1 for loan in loans.values() if loan["member_id"] == member_id and loan["status"] == ReturnStatus.ACTICE)

    if (member["membership_type"] == "premium" and member_loan_count >= 10) or (member["membership_type"] == "basic" and member_loan_count >= 3):
        raise LoanLimitExceededError(message="Member has exceeded the loan limit for their membership type.")

    loan_days = 30 if member["membership_type"] == "premium" else 14
    loan_id = max(loans.keys()) + 1 if loans else 1
    due_date = datetime.now(UTC) + timedelta(days=loan_days)

    loan_data = {
        "book_id": book_id,
        "member_id": member_id,
        "loan_date": datetime.now(UTC),
        "due_date": due_date,
        "return_date": None,
        "status": ReturnStatus.ACTICE
    }

    loans[loan_id] = loan_data
    book["available_copies"] -= 1

    return {"id": loan_id, **loan_data, "member": MemberOut(id=member_id, **member), "book": BookOut(id=book_id, **book)}

def get_loans_service(member_id: int | None, loan_status: ReturnStatus | None, pagination_params: PaginationParams):
    results = []
    for id, loan in loans.items():
        if (member_id and loan["member_id"] != member_id) or (loan_status and loan["status"] != loan_status):
            continue
        member, book = get_member_and_book_details(loan)
        results.append({"id": id, **loan, "member": member, "book": book})

    
    return pagination(pagination_params.skip, pagination_params.limit, results)

def get_overdue_loans_service(pagination_params: PaginationParams):
    results = []
    for id, loan in loans.items():
        if loan["status"] == ReturnStatus.ACTICE and loan["due_date"] < datetime.now(UTC):
            member, book = get_member_and_book_details(loan)
            results.append({"id": id, **loan, "member": member, "book": book})

    return pagination(pagination_params.skip, pagination_params.limit, results)

def get_loan_service(loan_id: int):
    loan = check_loan(loan_id)
    member, book = get_member_and_book_details(loan)
    return {"id": loan_id, **loan, "member": member, "book": book}

def return_loan_service(loan_id: int):
    loan = check_loan(loan_id)
    if loan["status"] == ReturnStatus.RETURNED:
        raise LoanNotFoundError(message="This loan has already been returned.")

    loan["return_date"] = datetime.now(UTC)
    loan["status"] = ReturnStatus.RETURNED

    book = check_book(loan["book_id"])
    book["available_copies"] += 1

    member, book = get_member_and_book_details(loan)
    return {"id": loan_id, **loan, "member": member, "book": book}