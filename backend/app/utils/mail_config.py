from app.config import settings
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_USER,
    MAIL_PASSWORD=settings.EMAIL_PASSWORD,
    MAIL_FROM=settings.EMAIL_USER,
    MAIL_FROM_NAME="Time Tracking System",
    MAIL_SERVER=settings.EMAIL_HOST,
    MAIL_PORT=settings.EMAIL_PORT,
     MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fast_mail = FastMail(conf)

async def send_email_async(subject: str, email_to: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=MessageType.plain
    )
    await fast_mail.send_message(message)
