import requests
from core.config import settings
from core.logger import logger


class BaltikaClient:
    def __init__(self):
        # API manzili config.py (va .env) orqali olinadi
        self.url = settings.BALTIKA_API_URL

    def send_xml(self, xml_content: bytes, report_type: str) -> bool:
        """
        Smartup'dan olingan XML faylni to'g'ridan-to'g'ri Baltika API'siga yuboradi.
        """
        if not self.url:
            logger.error("❌ Ошибка: В .env файле не указан BALTIKA_API_URL!")
            return False

        # XML baytlarini matnga o'giramiz
        try:
            xml_text = xml_content.decode('utf-8')
        except AttributeError:
            # Agar allaqachon matn (str) bo'lsa
            xml_text = xml_content

        # requests kutubxonasiga dictionary (lug'at) bersak,
        # u avtomatik "application/x-www-form-urlencoded" formatida yuboradi.
        payload = {
            "XMLData": xml_text
        }

        try:
            logger.info(f"📤 Отправка файла ({report_type}) на сервер Baltika (API)...")

            # Timeoutni 120 soniya qilamiz (katta hajmdagi fayllar va server javobi uchun)
            response = requests.post(self.url, data=payload, timeout=120)

            if response.status_code == 200:
                # Javobning faqat bosh qismini logga yozamiz (ekranni to'ldirib yubormasligi uchun)
                logger.info(f"✅ Успешно! Ответ Baltika: {response.text[:150]}...")
                return True
            else:
                logger.error(f"❌ Ошибка отправки (Статус {response.status_code}): {response.text[:300]}")
                return False

        except requests.exceptions.Timeout:
            logger.error(f"❌ Время ожидания ответа от Baltika API истекло (Timeout).")
            return False
        except Exception as e:
            logger.error(f"❌ Сетевая ошибка при отправке на Baltika: {e}")
            return False


# Boshqa fayllardan chaqirish uchun tayyor obyekt
baltika_client = BaltikaClient()