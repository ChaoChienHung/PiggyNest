from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.token import Token
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.category import Category
from app.core import security
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
):
    """
    Register a new user account into the system.
    Validates against existing emails and usernames, hashes the password, and writes to SQLite.
    """
    user = db.query(User).filter((User.email == user_in.email) | (User.username == user_in.username)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login system. 
    Returns a JWT Bearer token valid for 30 minutes to authenticate future REST requests.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/test-token", response_model=UserResponse)
def test_token(current_user: User = Depends(get_current_user)):
    """
    Diagnostic endpoint to verify if the provided Bearer token is valid and unexpired.
    Returns the parsed user profile.
    """
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's profile details (e.g. username).
    Checks for username collisions before committing.
    """
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="Username already taken")
    current_user.username = user_in.username
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me")
def delete_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Irreversibly delete the currently authenticated user's account.
    Cascades down and deletes all linked PiggyBanks, Transactions, and Categories.
    """
    piggy_banks = db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).all()
    if piggy_banks:
        pb_ids = [pb.id for pb in piggy_banks]
        db.query(Transaction).filter(Transaction.piggy_bank_id.in_(pb_ids)).delete(synchronize_session=False)
        db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).delete(synchronize_session=False)
    
    db.query(Category).filter(Category.user_id == current_user.id).delete(synchronize_session=False)
    
    db.delete(current_user)
    db.commit()
    return {"success": True}
