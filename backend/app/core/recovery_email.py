"""Send account recovery messages through a configured TLS SMTP server."""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def mail_is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_recovery_email(to_address: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT,
            context=ssl.create_default_context(), timeout=10,
        ) as smtp:
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Account recovery email could not be delivered")
