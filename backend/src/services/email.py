import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import settings


async def send_verification_email(to_email: str, code: str) -> None:
    """Отправить письмо с кодом подтверждения."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # В dev-режиме просто печатаем код в консоль
        print(f'[DEV] Код подтверждения для {to_email}: {code}')
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Подтверждение регистрации — TeamPal'
    msg['From'] = settings.SMTP_FROM or settings.SMTP_USER
    msg['To'] = to_email

    text = f'Ваш код подтверждения: {code}\n\nКод действителен 10 минут.'
    html = f"""
    <html>
      <body>
        <p>Добро пожаловать в <strong>TeamPal</strong>!</p>
        <p>Ваш код подтверждения:</p>
        <h2 style="letter-spacing: 8px; font-size: 36px; color: #2E5FA3;">{code}</h2>
        <p style="color: #888;">Код действителен 10 минут.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        print(f'[EMAIL ERROR] Не удалось отправить письмо на {to_email}: {e}')
        print(f'[DEV FALLBACK] Код подтверждения для {to_email}: {code}')
