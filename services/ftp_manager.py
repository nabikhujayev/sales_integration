import os
from ftplib import FTP
from typing import List
from core.config import settings
from core.logger import logger


class FTPManager:
    def __init__(self):
        self.host = settings.SFTP_SERVER
        self.port = settings.SFTP_PORT or 21
        self.username = settings.SFTP_USERNAME
        self.password = settings.SFTP_PASSWORD
        self.remote_path = settings.SFTP_REMOTE_PATH

    def upload_files(self, file_paths: List[str]) -> bool:
        """
        Fayllarni FTP serverga yuklash.
        """
        if not file_paths:
            return False

        ftp = FTP()
        try:
            logger.info(f"Подключение к FTP-серверу: {self.host}:{self.port}")

            # 1. Ulanish
            ftp.connect(self.host, self.port, timeout=30)
            ftp.login(self.username, self.password)
            logger.info("Авторизация FTP успешна.")

            # 2. Papkaga kirish
            if self.remote_path:
                try:
                    ftp.cwd(self.remote_path)
                except Exception:
                    logger.warning(f"Не удалось перейти в каталог: {self.remote_path}, загрузка будет выполнена в корневую папку.")

            # 3. Fayllarni yuklash
            uploaded_count = 0
            for local_path in file_paths:
                filename = os.path.basename(local_path)
                logger.info(f"Загрузка через FTP: {filename}")

                with open(local_path, 'rb') as f:
                    # 'STOR filename' komandasi bilan yuklaymiz
                    ftp.storbinary(f'STOR {filename}', f)

                logger.info(f"✅ Загружен: {filename}")
                uploaded_count += 1

            # 4. Ulanishni yopish
            ftp.quit()

            if uploaded_count == len(file_paths):
                logger.info(f"SUCCESS: Все {uploaded_count} файлов отправлены на FTP.")
                return True
            return False

        except Exception as e:
            logger.error(f"Ошибка FTP: {e}")
            try:
                ftp.close()
            except:
                pass
            return False


# Singleton
ftp_manager = FTPManager()