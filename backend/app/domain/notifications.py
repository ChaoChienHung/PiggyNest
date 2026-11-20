from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    kind: str = "info",
    event_key: Optional[str] = None,
) -> Notification:
    """
    Create an in-app notification for a user.

    When `event_key` is provided, returns the existing notification if one with
    the same `(user_id, event_key)` already exists, guaranteeing idempotency across
    restarts or repeated triggers.
    """
    if event_key is not None:
        existing = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.event_key == event_key)
            .first()
        )
        if existing is not None:
            return existing

    note = Notification(
        user_id=user_id,
        kind=kind,
        title=title,
        body=body,
        event_key=event_key,
    )
    db.add(note)
    return note
