import requests
import io
import zipfile
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from core.config import settings
from core.logger import logger


class SmartupClient:
    def __init__(self):
        self.base_url = settings.SMARTUP_SERVER_URL
        self.token = None

    def _get_oauth_token(self) -> str:
        """Smartup tizimidan OAuth2 access token oladi."""
        logger.info("🔑 Получение OAuth токена Smartup...")
        url = f"{self.base_url}/security/oauth/token"

        # Payload
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.SMARTUP_CLIENT_ID,
            "client_secret": settings.SMARTUP_CLIENT_SECRET,
            "scope": "read"
        }

        try:
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code != 200:
                logger.error(f"❌ Ошибка при получении токена: {response.text}")
                response.raise_for_status()

            data = response.json()

            # --- O'ZGARISH: Tokenni tekshirish ---
            access_token = data.get('access_token')
            if not access_token:
                raise Exception("В ответе токена отсутствует 'access_token'!")

            final_token = f"Bearer {access_token}"

            logger.info(f"✅ Токен успешно получен (Начало: {final_token[:15]}...)")

            return final_token

        except Exception as e:
            logger.error(f"Критическая ошибка при получении токена: {e}")
            raise e

    def _ensure_token(self):
        if not self.token:
            self.token = self._get_oauth_token()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def download_sales_report(self, template_id: int) -> bytes:
        self._ensure_token()

        url = f"{self.base_url}/trade/rep/integration/saleswork"

        end_date = datetime.today() - timedelta(days=1)
        begin_date = end_date - timedelta(days=settings.DAYS_DIFF)

        payload = {
            "begin_date": begin_date.strftime('%d.%m.%Y'),
            "end_date": end_date.strftime('%d.%m.%Y'),
            "period_type": settings.PERIOD_TYPE,
            "company_id": settings.COMPANY_ID,
            "filial_id": settings.FILIAL_ID,
            "template_id": template_id
        }

        logger.info(
            f"📤 Отправка запроса (Шаблон: {template_id}, Дата: {payload['begin_date']} - {payload['end_date']})")

        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=1800)

        # XATOLIKNI QAYTA ISHLASH
        if response.status_code != 200:
            try:
                error_text = response.text
            except:
                error_text = "Не удалось прочитать"

            logger.error(f"❌ Ответ сервера (Статус {response.status_code}): {error_text[:300]}")

            # Agar "Avtorizatsiya kerak" degan HTML xato kelsa yoki 401 bo'lsa
            if response.status_code == 401 or "authorization" in error_text.lower() or "авторизация" in error_text.lower():
                logger.warning("🔄 Токен устарел или недействителен. Попытка обновления...")
                self.token = None
                # Retry ishlashi uchun exception otamiz
                raise Exception("Authorization Failed - Retrying")

            raise Exception(f"Ошибка Smartup API: {response.status_code}")

        # YUKLASH JARAYONI
        buffer = io.BytesIO()
        total_size = 0
        chunk_size = 1024 * 1024

        logger.info("📥 Начался поток данных (Stream)...")

        for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
            if chunk:
                buffer.write(chunk)
                total_size += len(chunk)
                if i % 5 == 0:  # Har 5MB da log
                    logger.info(f"⏳ Загрузка... {total_size / (1024 * 1024):.2f} MB")

        logger.info(f"✅ Загрузка завершена. Всего: {total_size / (1024 * 1024):.2f} MB")

        buffer.seek(0)
        file_content = buffer.read()

        # ZIP TEKSHIRUVI
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                if zf.testzip() is not None:
                    raise Exception("Внутренняя структура ZIP-файла повреждена")
        except zipfile.BadZipFile:
            # Agar HTML qaytgan bo'lsa, uni ko'ramiz
            logger.error(f"❌ Полученный файл не является ZIP! Ответ сервера (начало): {file_content[:500]}")
            raise Exception("Сервер не вернул ZIP-файл. Возможно, снова ошибка авторизации.")

        return file_content

    # === YANGI QO'SHILGAN QISM (MONOLIT UCHUN) ===
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def download_monolit_report(self, report_type: str) -> bytes:
        self._ensure_token()

        # URL ni to'g'rilaymiz (: va /b/ bilan)
        url = f"{self.base_url}/b/trade/rep/integration/integration_two{report_type}"

        # Bugungi kun (tugash sanasi)
        end_date_obj = datetime.today()
        # 4 kun oldingi sana (boshlanish sanasi) - jami 5 kunlik oraliq bo'ladi
        begin_date_obj = end_date_obj - timedelta(days=4)

        payload = {
            "begin_date": begin_date_obj.strftime('%d.%m.%Y'),
            "end_date": end_date_obj.strftime('%d.%m.%Y'),
            "filial_id": []
        }

        logger.info(f"📤 Отправка запроса Monolit (Тип: {report_type}, URL: {url})")

        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

        # Timeoutni 600 soniya (10 minut) qilib qo'yamiz, Monolit og'ir report bo'lishi mumkin
        response = requests.post(url, json=payload, headers=headers, timeout=600)

        if response.status_code != 200:
            error_text = response.text[:300]
            logger.error(f"❌ Ответ сервера Monolit (Статус {response.status_code}): {error_text}")
            if response.status_code == 401:
                self.token = None
                raise Exception("Authorization Failed - Retrying")
            raise Exception(f"Ошибка Monolit API: {response.status_code}")

        file_content = response.content
        logger.info(f"✅ Успешно скачан отчет Monolit ({report_type}), размер: {len(file_content) / 1024:.2f} KB")

        return file_content


smartup_client = SmartupClient()