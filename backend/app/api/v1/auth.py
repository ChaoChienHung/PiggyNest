from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import secrets
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, CurrencyRateUpdate, CurrencyRateResponse, Currency
from app.schemas.token import Token
from app.models.piggy_bank import PiggyBank
from app.models.transaction import Transaction
from app.models.category import Category
from app.core import security
from app.core.config import settings
from app.core.recovery_email import mail_is_configured, send_recovery_email
from app.models.recovery import RecoveryChallenge
from app.models.currency_rate import CurrencyRate
from app.domain.default_rates import DEFAULT_SGD_TO_NTD
from app.schemas.recovery import PasswordResetConfirm, RecoveryEmail
from app.api.deps import get_current_user

router = APIRouter()
RECOVERY_MESSAGE = {"message": "If this email belongs to an active account, a message will be sent."}


def _utc_now_naive() -> datetime:
    """UTC timestamp stored as naive datetime to match SQLite DateTime comparisons."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
RECOVERY_COOLDOWN = timedelta(seconds=60)
RESET_LIFETIME = timedelta(minutes=10)
MAX_RESET_ATTEMPTS = 5


def _recovery_mail_available():
    if not mail_is_configured():
        raise HTTPException(status_code=503, detail="Account recovery email is not configured")


def _challenge(db: Session, user_id: int) -> RecoveryChallenge:
    challenge = db.get(RecoveryChallenge, user_id)
    if challenge is None:
        challenge = RecoveryChallenge(user_id=user_id)
        db.add(challenge)
    return challenge


def _code_digest(user_id: int, code: str) -> str:
    value = f"reset:{user_id}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), value, sha256).hexdigest()


@router.post("/recovery/username", status_code=202)
def remind_username(
    payload: RecoveryEmail, background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _recovery_mail_available()
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if user:
        challenge = _challenge(db, user.id)
        now = _utc_now_naive()
        if not challenge.username_sent_at or now - challenge.username_sent_at >= RECOVERY_COOLDOWN:
            challenge.username_sent_at = now
            db.commit()
            background_tasks.add_task(
                send_recovery_email, user.email, "PiggyNest username reminder",
                f"Your PiggyNest username is: {user.username}\n\nIf you did not request this, you can ignore this email.",
            )
    return RECOVERY_MESSAGE


@router.post("/recovery/password", status_code=202)
def request_password_reset(
    payload: RecoveryEmail, background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _recovery_mail_available()
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if user:
        challenge = _challenge(db, user.id)
        now = _utc_now_naive()
        if not challenge.reset_sent_at or now - challenge.reset_sent_at >= RECOVERY_COOLDOWN:
            code = f"{secrets.randbelow(10**8):08d}"
            challenge.code_digest = _code_digest(user.id, code)
            challenge.expires_at = now + RESET_LIFETIME
            challenge.attempts = 0
            challenge.reset_sent_at = now
            db.commit()
            background_tasks.add_task(
                send_recovery_email, user.email, "PiggyNest password reset code",
                f"Your PiggyNest password reset code is {code}. It expires in 10 minutes.\n\nIf you did not request this, you can ignore this email.",
            )
    return RECOVERY_MESSAGE


@router.post("/recovery/password/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    challenge = db.get(RecoveryChallenge, user.id) if user else None
    now = _utc_now_naive()
    invalid = HTTPException(status_code=400, detail="Invalid or expired reset code")
    if (not user or not challenge or not challenge.code_digest or not challenge.expires_at
            or now >= challenge.expires_at or challenge.attempts >= MAX_RESET_ATTEMPTS):
        raise invalid
    if not hmac.compare_digest(challenge.code_digest, _code_digest(user.id, payload.code)):
        challenge.attempts += 1
        if challenge.attempts >= MAX_RESET_ATTEMPTS:
            challenge.code_digest = None
        db.commit()
        raise invalid
    user.hashed_password = security.get_password_hash(payload.new_password)
    user.token_version += 1
    challenge.code_digest = None
    challenge.expires_at = None
    db.commit()
    return {"message": "Password updated. Sign in with your new password."}

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
    db.flush()
    db.add(CurrencyRate(
        user_id=user.id, currency="SGD", rate_to_ntd=DEFAULT_SGD_TO_NTD,
    ))
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
            user.id, expires_delta=access_token_expires, token_version=user.token_version,
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
    if user_in.username:
        existing = db.query(User).filter(User.username == user_in.username).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = user_in.username
    if user_in.password:
        current_user.hashed_password = security.get_password_hash(user_in.password)
        current_user.token_version += 1
    if user_in.transactions_per_page is not None:
        current_user.transactions_per_page = user_in.transactions_per_page
    if user_in.date_format is not None:
        current_user.date_format = user_in.date_format
    if user_in.display_currency is not None:
        current_user.display_currency = user_in.display_currency
    if user_in.net_worth_hidden is not None:
        current_user.net_worth_hidden = user_in.net_worth_hidden
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/rates", response_model=list[CurrencyRateResponse])
def list_currency_rates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return db.query(CurrencyRate).filter(CurrencyRate.user_id == current_user.id).order_by(CurrencyRate.currency).all()


@router.put("/me/rates/{currency}", response_model=CurrencyRateResponse)
def set_currency_rate(
    currency: Currency, payload: CurrencyRateUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    if currency == "NTD":
        raise HTTPException(status_code=422, detail="NTD is the reference currency and does not need a rate")
    rate = db.query(CurrencyRate).filter(
        CurrencyRate.user_id == current_user.id, CurrencyRate.currency == currency,
    ).first()
    if rate is None:
        rate = CurrencyRate(user_id=current_user.id, currency=currency)
        db.add(rate)
    rate.rate_to_ntd = payload.rate_to_ntd
    rate.updated_at = _utc_now_naive()
    db.commit()
    db.refresh(rate)
    return rate

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
    db.query(CurrencyRate).filter(CurrencyRate.user_id == current_user.id).delete(synchronize_session=False)
    db.query(RecoveryChallenge).filter(RecoveryChallenge.user_id == current_user.id).delete(synchronize_session=False)
    
    db.delete(current_user)
    db.commit()
    return {"success": True}
