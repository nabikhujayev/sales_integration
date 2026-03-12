import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 1. SMARTUP ASOSIY SOZLAMALAR
    SMARTUP_SERVER_URL: str
    SMARTUP_CLIENT_ID: str
    SMARTUP_CLIENT_SECRET: str
    COMPANY_NAME: str
    COMPANY_ID: int
    FILIAL_ID: int

    # 2. SALESWORK SOZLAMALAR (01:00 uchun)
    TEMPLATE_ID: str = ""
    PERIOD_TYPE: str = "L90D"
    DAYS_DIFF: int = 90

    # 3. SFTP/FTP SOZLAMALAR (Saleswork uchun)
    PROTOCOL: str = "SFTP"
    SFTP_SERVER: str = ""
    SFTP_PORT: int = 22
    SFTP_USERNAME: str = ""
    SFTP_PASSWORD: str = ""
    SFTP_REMOTE_PATH: str = "/"

    # 4. MONOLIT SOZLAMALAR (20:00 uchun - API orqali jo'natishga)
    ENABLE_XML_TRANSFORMATION: bool = False
    MONOLIT_REPORT_TYPES: str = ""
    BALTIKA_API_URL: str = ""  # Monolit jo'natiladigan manzil

    # 5. BOSHQA SOZLAMALAR
    ENABLE_MONOLIT_REPORT: bool = False
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_RECIPIENTS: str
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = os.getenv("ENV_FILE_PATH", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def get_template_ids(self) -> List[int]:
        if not self.TEMPLATE_ID:
            return []
        try:
            return [int(t.strip()) for t in str(self.TEMPLATE_ID).split(",") if t.strip()]
        except ValueError:
            # Agar kutilmagan belgi (harf) bo'lsa, xato bermay bo'sh ro'yxat qaytaradi
            return []

    @property
    def get_monolit_report_types(self) -> List[str]:
        if not self.MONOLIT_REPORT_TYPES:
            return []
        return [t.strip() for t in self.MONOLIT_REPORT_TYPES.split(",") if t.strip()]

    @property
    def recipient_list(self) -> List[str]:
        if not self.EMAIL_RECIPIENTS:
            return []
        return [email.strip() for email in self.EMAIL_RECIPIENTS.split(",") if email.strip()]


settings = Settings()