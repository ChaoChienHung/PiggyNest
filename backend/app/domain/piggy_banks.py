import re
from app.db.repositories.piggy_bank_repo import PiggyBankRepository

NAME_PATTERN = re.compile(r"^[\w\-]+$")

def create_piggy_bank(
    user_id: int,
    name: str,
    currency: str,
    repo: PiggyBankRepository,
):
    if not NAME_PATTERN.match(name):
        raise ValueError(
            "Invalid piggy bank name. Use alphanumeric, hyphen, underscore."
        )

    existing = repo.get_by_name(user_id, name)
    if existing:
        raise ValueError("Piggy bank already exists for this user")

    return repo.create(user_id, name, currency)

def list_piggy_banks(user_id: int, repo: PiggyBankRepository):
    return repo.list_by_user(user_id)
