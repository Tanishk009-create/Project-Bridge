"""Generic transactional mail. File delivery is for local development only."""
from email.message import EmailMessage
from pathlib import Path
import smtplib
import uuid
from app.core import settings


def send_mail(address: str, subject: str, body: str) -> str:
    if settings.mail_mode == "disabled":
        return "disabled"
    if settings.mail_mode == "file":
        outbox = Path(".tmp/mail-outbox")
        outbox.mkdir(parents=True, exist_ok=True)
        path = outbox / f"{uuid.uuid4().hex}.txt"
        path.write_text(f"To: {address}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
        return "local-file"
    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError("SMTP_HOST and SMTP_FROM must be configured for email delivery")
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = address
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
        if settings.smtp_starttls:
            client.starttls()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        client.send_message(message)
    return "sent"
