import paramiko
import os
import socket
import time
from typing import List
from core.config import settings
from core.logger import logger


class SFTPManager:
    """
    SFTP server bilan xavfsiz va barqaror muloqot qilish uchun manager.
    Ulanishni boshqarish va fayllarni uzatishni ta'minlaydi.
    """

    def __init__(self):
        self.host = settings.SFTP_SERVER
        self.port = settings.SFTP_PORT
        self.username = settings.SFTP_USERNAME
        self.password = settings.SFTP_PASSWORD
        self.remote_path = settings.SFTP_REMOTE_PATH

        self.ssh = None
        self.sftp = None

    def _connect(self):
        """SSH va SFTP sessiyasini ochadi."""
        try:
            logger.info(f"Установка соединения с SFTP-сервером: {self.host}")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=60,
                banner_timeout=30,
                look_for_keys=False,
                allow_agent=False,
                compress=True
            )
            self.sftp = self.ssh.open_sftp()
            logger.info("SFTP-соединение успешно установлено.")

        except paramiko.AuthenticationException:
            logger.error("Ошибка аутентификации SFTP: Неверный логин или пароль.")
            raise
        except Exception as e:
            logger.error(f"Ошибка при подключении к SFTP: {e}")
            raise

    def _close(self):
        """Ulanishlarni xavfsiz yopadi."""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        logger.info("Соединения SFTP закрыты.")

    def upload_files(self, file_paths: List[str]) -> bool:
        """
        Berilgan fayllar ro'yxatini SFTP serverga yuklaydi.
        """
        if not file_paths:
            logger.warning("Файлы для загрузки не найдены.")
            return False

        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                self._connect()

                # Monolit papkasi allaqachon tekshirildimi yoki yo'qligini bilish uchun belgi
                monolit_dir_checked = False

                uploaded_count = 0
                for local_path in file_paths:
                    file_name = os.path.basename(local_path)

                    # --- O'ZGARISH SHU YERDA: MONOLIT FAYLLAR UCHUN ALOHIDA MANTIQ ---
                    if file_name.startswith("monolit_"):
                        monolit_remote_dir = f"{self.remote_path}/monolit"

                        # Papkani faqat bir marta tekshiramiz/yaratamiz
                        if not monolit_dir_checked:
                            try:
                                self.sftp.stat(monolit_remote_dir)
                            except IOError:
                                # Agar papka yo'q bo'lsa (IOError), uni yaratamiz
                                logger.info(f"📁 Папка 'monolit' не найдена на сервере. Создаем: {monolit_remote_dir}")
                                self.sftp.mkdir(monolit_remote_dir)
                            monolit_dir_checked = True

                        remote_full_path = f"{monolit_remote_dir}/{file_name}"
                        logger.info(f"Отправка файла Monolit в отдельную папку: {file_name}")
                    else:
                        # Oddiy (saleswork) fayllar uchun eski mantiq
                        remote_full_path = f"{self.remote_path}/{file_name}"
                        logger.info(f"Отправка файла: {file_name}")

                    # Faylni serverga joylash
                    self.sftp.put(local_path, remote_full_path)
                    uploaded_count += 1
                    logger.info(f"✅ Успешно отправлен: {file_name}")

                if uploaded_count == len(file_paths):
                    logger.info(f"SUCCESS: Все {uploaded_count} файлов загружены на SFTP.")
                    return True

            except (socket.error, paramiko.SSHException, EOFError, IOError) as e:
                attempt += 1
                logger.warning(f"Ошибка соединения (Попытка {attempt}/{max_attempts}): {e}")
                time.sleep(15)
            finally:
                self._close()

        logger.error("ERROR: Не удалось загрузить файлы на SFTP.")
        return False


# Singleton instance
sftp_manager = SFTPManager()