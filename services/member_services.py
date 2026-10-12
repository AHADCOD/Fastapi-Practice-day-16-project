from core.exceptions import DuplicateEmailError, MemberNotFoundError
from schemas.members import MembershipType
from core.dependencies import PaginationParams, pagination

members = {}

def check_member(member_id: int):
    if member_id not in list(members.keys()):
        raise MemberNotFoundError(message=f"Member with ID {member_id} does not exist.")
    return members[member_id]

    
def create_member_service(member: dict):
    id = max(list(members.keys()))+1 if members else 1

    for i, value in members.items():
        if member["email"].lower() == value["email"].lower():
            raise DuplicateEmailError(message="Duplicate Email. Member of this email already exits.")

    members[id] = member
    return {"id": id, **member}

def get_members_service(membership_type: MembershipType | None, pagination_params: PaginationParams):
    result = []
    for i, value in members.items():
        if membership_type and value["membership_type"] == membership_type:
            result.append({"id": i, **value})
        if not membership_type:
            result.append({"id": i, **value})
    return pagination(pagination_params.skip, pagination_params.limit, result)


def get_member_service(member_id: int):
    member = check_member(member_id)
    return {"id": member_id, **member}

def update_member_service(member_id: int, member: dict):
    existing_member = check_member(member_id)

    for i, value in members.items():
        if member.get("email") and (member["email"].lower() == value["email"].lower()) and (i != member_id):
            raise DuplicateEmailError(message="Duplicate Email. Member of this email already exits.")
    for key, value in member.items():
        existing_member[key] = value
    members[member_id] = existing_member
    return {"id": member_id, **existing_member}
    