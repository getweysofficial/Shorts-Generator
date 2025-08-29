import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import get_settings

from loguru import logger

logger = logger.bind(name="Mail Sender")
settings = get_settings()



def send_email(to, shorts_paths):
    subject = "Your Shorts Are Ready 🎬"

    links_html = "".join(
        f'<li><a href="{url}" target="_blank">{os.path.basename(url)}</a></li>'
        for url in shorts_paths
    )

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">✨ Your Shorts Are Ready!</h2>
        <p>Hello,</p>
        <p>We’ve finished generating your video shorts. You can watch or download them using the links below:</p>
        <ul style="padding-left: 20px;">
          {links_html}
        </ul>
        <p style="margin-top: 20px;">Cheers,<br><b>The RawClip Team</b> 🎬</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SENDER_EMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.SENDER_EMAIL_ADDRESS, settings.APP_PASSWORD)
        server.sendmail(settings.SENDER_EMAIL_ADDRESS, to, msg.as_string())
    logger.info(f"Email sent to {to}")

