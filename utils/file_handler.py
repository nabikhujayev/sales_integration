import os
import zipfile
import io
import shutil
from typing import List
from datetime import datetime
from core.logger import logger


class FileHandler:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
        self.temp_dir = os.path.join(self.base_path, "temp_extract")
        self.backups_dir = os.path.join(self.base_path, "backups")

    # === ESKI FUNKSIYALAR (SALESWORK ZIP UCHUN) ===

    def save_zip_to_backup(self, content: bytes) -> str:
        """Сохраняет полученные байты как ZIP-файл в папку резервного копирования."""
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)

        # Fayl nomini yaratish
        timestamp_full = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_path = os.path.join(self.backups_dir, f'report_{timestamp_full}.zip')

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Резервная копия сохранена: {os.path.basename(file_path)}")
        return file_path

    def extract_zip(self, zip_content: bytes) -> List[str]:
        """
        Распаковывает ZIP-файл во временную папку.
        Возвращает список ТОЛЬКО тех файлов, которые были в этом архиве.
        """
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        new_xml_files = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                zf.extractall(self.temp_dir)

                for file_name in zf.namelist():
                    # Faqat XML fayllarni olamiz
                    if file_name.lower().endswith('.xml'):
                        # To'liq yo'lni yasaymiz
                        full_path = os.path.join(self.temp_dir, file_name)
                        # Agar ZIP ichida papkalar bo'lsa, ularni to'g'ri slash bilan to'g'rilaymiz
                        full_path = os.path.normpath(full_path)
                        new_xml_files.append(full_path)

            logger.info(f"ZIP-файл распакован. Извлечено XML из архива: {len(new_xml_files)} шт.")

        except Exception as e:
            logger.error(f"Ошибка при распаковке ZIP: {e}")
            raise e

        return new_xml_files

    # === YANGI QO'SHILGAN FUNKSIYALAR (MONOLIT UCHUN) ===

    def save_monolit_to_backup(self, content: bytes, report_type: str) -> str:
        """Сохраняет сырой XML файл отчета Monolit в папку бэкапов."""
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)

        # XAVFLI BELGILARNI TOZALASH (Windows xato bermasligi uchun)
        safe_report_type = report_type.replace(":", "_").replace("$", "_")

        timestamp_full = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_name = f'monolit_{safe_report_type}_{timestamp_full}.xml'
        file_path = os.path.join(self.backups_dir, file_name)

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Резервная копия Monolit сохранена: {file_name}")
        return file_path

    def save_monolit_to_temp(self, content: bytes, report_type: str) -> List[str]:
        """Сохраняет XML файл отчета Monolit во временную папку."""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # XAVFLI BELGILARNI TOZALASH (Windows xato bermasligi uchun)
        safe_report_type = report_type.replace(":", "_").replace("$", "_")

        file_name = f"monolit_{safe_report_type}.xml"
        file_path = os.path.join(self.temp_dir, file_name)

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Файл Monolit подготовлен к отправке: {file_name}")
        return [file_path]

    # === TOZALASH FUNKSIYALARI ===

    def cleanup_temp(self):
        """Удаляет временно распакованные файлы."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Временная папка очищена.")
            except Exception as e:
                logger.error(f"Ошибка при удалении временной папки: {e}")

    def clear_old_backups(self, days: int = 7):
        """Удаление старых файлов резервных копий."""
        self.cleanup_temp()
        if os.path.exists(self.backups_dir):
            logger.info("Старые бэкапы и временная папка очищены.")


# Singleton instance
file_handler = FileHandler()