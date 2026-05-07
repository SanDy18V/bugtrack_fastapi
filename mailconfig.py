from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="yourgmail@gmail.com",
    MAIL_PASSWORD="your_app_password",
    MAIL_FROM="yourgmail@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_verification_email(email, token):

    verification_link = f"http://127.0.0.1:8000/verify/{token}"

    print(f"Sending mail to {email}")
    print(verification_link)

    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=f"""
        Click the link below to verify your account:

        {verification_link}
        """,
        subtype="plain"
    )

    fm = FastMail(conf)

    await fm.send_message(message)

    print("Email sent successfully")