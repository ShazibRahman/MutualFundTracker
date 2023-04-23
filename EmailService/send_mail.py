
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage


class EmailService:
    def __init__(self):
        self.email = os.environ.get("shazmail")
        self.password = os.environ.get("shazPassword")
        self.ctx = ssl.create_default_context()
        self.ctx.verify_mode = ssl.CERT_REQUIRED

    def create_message(self, to_email, subject, body):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email
        msg["To"] = to_email
        msg.set_content(body)
        return msg

    def send_mail(self, to_email=None, subject="Subject", body="Body"):
        if to_email is None:
            to_email = self.email
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=self.ctx) as server:
                server.login(self.email, self.password)
                server.send_message(
                    self.create_message(to_email, subject, body))
        except Exception as e:
            logging.error("---Network Error---")
            logging.error(str(e))
            return False
        return True
