import logging
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.models import EmailTemplate, SMTPAccount
from app.services.encryption import decrypt_secret

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_template(html: str, subject: str, variables: dict[str, str]) -> tuple[str, str]:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    html_out = VARIABLE_PATTERN.sub(repl, html)
    subject_out = VARIABLE_PATTERN.sub(repl, subject)
    return html_out, subject_out


def send_smtp_sync(
    account: SMTPAccount,
    template: EmailTemplate,
    to_email: str,
    variables: dict[str, str] | None = None,
) -> None:
    variables = variables or {}
    variables.setdefault("email", to_email)
    password = decrypt_secret(account.password_encrypted)
    html_body, subject = render_template(template.html_content, template.subject, variables)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((account.from_name or "", account.from_email))
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    if account.use_tls:
        with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=60) as server:
            server.starttls(context=context)
            server.login(account.username, password)
            server.sendmail(account.from_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP_SSL(account.smtp_host, account.smtp_port, timeout=60, context=context) as server:
            server.login(account.username, password)
            server.sendmail(account.from_email, [to_email], msg.as_string())


def test_smtp_connection(account: SMTPAccount) -> None:
    password = decrypt_secret(account.password_encrypted)
    context = ssl.create_default_context()
    if account.use_tls:
        with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30) as server:
            server.starttls(context=context)
            server.login(account.username, password)
    else:
        with smtplib.SMTP_SSL(account.smtp_host, account.smtp_port, timeout=30, context=context) as server:
            server.login(account.username, password)


def test_smtp_raw(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password_plain: str,
    use_tls: bool,
) -> None:
    context = ssl.create_default_context()
    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls(context=context)
            server.login(username, password_plain)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=context) as server:
            server.login(username, password_plain)
