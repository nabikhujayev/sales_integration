import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List
from core.config import settings
from core.logger import logger

class MailService:
    def __init__(self):
        self.sender = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD
        self.recipients = settings.recipient_list
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT

    def send_report(self, subject: str, body: str, logs: List[str] = None):
        """
        Email yuborish servisi.
        """

        full_content = f"ОТЧЕТ ОТ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        full_content += "=" * 40 + "\n"
        full_content += f"СТАТУС: {body}\n"
        full_content += "=" * 40 + "\n\n"

        if logs:
            full_content += "ПОДРОБНЫЕ ЛОГИ:\n"
            for line in logs:
                full_content += line + "\n"

        for recipient in self.recipients:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.sender
                msg['To'] = recipient
                msg['Subject'] = subject  # To'g'ridan-to'g'ri mavzu qo'yiladi
                msg.attach(MIMEText(full_content, 'plain', 'utf-8'))

                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender, self.password)
                    server.send_message(msg)

                logger.info(f"Email успешно отправлен: {recipient}")
            except Exception as e:
                logger.error(f"Ошибка при отправке Email ({recipient}): {e}")


# Singleton
mail_service = MailService()