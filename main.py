import sys
import os
from datetime import datetime
from typing import List
from core.config import settings
from core.logger import logger
from core.exceptions import SayonarBaseError, SFTPError
from services.smartup_client import smartup_client
from services.sftp_manager import sftp_manager
from services.ftp_manager import ftp_manager
from services.mail_service import mail_service
from utils.file_handler import file_handler
from services.xml_transformer import xml_transformer
from services.baltika_client import baltika_client


def run_integration(job_type="all"):
    current_logs: List[str] = []

    # Log yozish yordamchisi
    def custom_log(message: str, level: str = "info"):
        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        current_logs.append(log_msg)

        if level == "info":
            logger.info(message)
        elif level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)

    # Bu sessiyada yaratilgan backup fayllar ro'yxati
    session_backup_files: List[str] = []

    try:
        custom_log(f"🚀 Запуск интеграции: {settings.COMPANY_NAME} (Режим: {job_type.upper()})")

        # 1. Tozalash (Jarayon boshida eski temp fayllarni tozalaymiz)
        file_handler.clear_old_backups()

        all_xml_files = []

        # =====================================================================
        # 1-QISM: SALESWORK (01:00 da ishlaydi, SFTP/FTP ga yuboradi)
        # =====================================================================
        if job_type in ["all", "saleswork"]:
            template_ids = settings.get_template_ids
            if template_ids:
                custom_log(f"📦 Запуск обработки Saleswork. Шаблоны: {template_ids}")
                saleswork_files = []

                # A. Yuklab olish va Extract qilish
                for t_id in template_ids:
                    try:
                        custom_log(f"📥 Скачивание шаблона ID: {t_id}...")
                        zip_content = smartup_client.download_sales_report(template_id=t_id)

                        backup_path = file_handler.save_zip_to_backup(zip_content)
                        session_backup_files.append(backup_path)

                        extracted = file_handler.extract_zip(zip_content)
                        if extracted:
                            saleswork_files.extend(extracted)
                            custom_log(f"✅ Шаблон {t_id}: получено {len(extracted)} XML файлов.")
                        else:
                            custom_log(f"⚠️ Шаблон {t_id}: XML файлы не найдены.", level="warning")
                    except Exception as e:
                        custom_log(f"❌ Ошибка с шаблоном {t_id}: {e}", level="error")

                # B. Transformatsiya va Serverga yuklash
                if saleswork_files:
                    saleswork_files = list(set(saleswork_files))

                    if settings.ENABLE_XML_TRANSFORMATION:
                        custom_log("🔄 Начало: XML Трансформация (замена AREA_ID)...")
                        for xml_file in saleswork_files:
                            if os.path.basename(xml_file).lower() == "outlets.xml":
                                try:
                                    if xml_transformer.process_outlets(xml_file):
                                        custom_log(f"✅ AREA_ID обновлен: {os.path.basename(xml_file)}")
                                except Exception as trans_error:
                                    custom_log(f"⚠️ Ошибка трансформации: {trans_error}", level="warning")

                    protocol = getattr(settings, "PROTOCOL", "SFTP")
                    custom_log(f"📤 Отправка Saleswork на сервер ({protocol})...")

                    if protocol == "FTP":
                        success = ftp_manager.upload_files(saleswork_files)
                    else:
                        success = sftp_manager.upload_files(saleswork_files)

                    if not success:
                        raise SFTPError(f"Ошибка при загрузке файлов Saleswork на сервер ({protocol}).")
                    else:
                        custom_log("✅ Файлы Saleswork успешно загружены на сервер.")

        # =====================================================================
        # 2-QISM: MONOLIT (20:00 da ishlaydi, BALTIKA API'ga yuboradi)
        # =====================================================================
        if job_type in ["all", "monolit"]:
            if getattr(settings, "ENABLE_MONOLIT_REPORT", False):
                monolit_types = settings.get_monolit_report_types
                if monolit_types:
                    custom_log(f"📦 Запуск обработки Monolit. Отчеты: {monolit_types}")

                    for rep_type in monolit_types:
                        try:
                            custom_log(f"📥 Скачивание отчета Monolit: {rep_type}...")

                            # A. XML yuklab olish
                            monolit_content = smartup_client.download_monolit_report(report_type=rep_type)

                            # B. Backup olish (Xavfsizlik uchun)
                            backup_path = file_handler.save_monolit_to_backup(monolit_content, rep_type)
                            session_backup_files.append(backup_path)

                            # C. To'g'ridan-to'g'ri Baltika API ga yuborish (SFTP qilinmaydi!)
                            is_sent = baltika_client.send_xml(xml_content=monolit_content, report_type=rep_type)

                            if is_sent:
                                custom_log(f"✅ Отчет Monolit ({rep_type}) успешно отправлен через API.")
                            else:
                                custom_log(f"❌ Ошибка отправки Monolit ({rep_type}) через API.", level="error")

                        except Exception as e:
                            custom_log(f"❌ Ошибка с Monolit отчетом {rep_type}: {e}", level="error")

        # =====================================================================
        # YAKUNIY XABARNOMA
        # =====================================================================
        success_msg = f"SUCCESS - Задачи для {settings.COMPANY_NAME} ({job_type.upper()}) завершены."
        custom_log(success_msg)
        mail_service.send_report(
            subject=f"✅ {settings.COMPANY_NAME} - {job_type.upper()} завершен",
            body=success_msg,
            logs=current_logs
        )

    except SayonarBaseError as e:
        error_text = f"Ошибка проекта ({settings.COMPANY_NAME}): {e.message}"
        custom_log(error_text, level="error")
        mail_service.send_report(subject=f"❌ {settings.COMPANY_NAME} - Ошибка", body=error_text, logs=current_logs)
        sys.exit(1)

    except Exception as e:
        error_text = f"Критическая ошибка ({settings.COMPANY_NAME}): {str(e)}"
        custom_log(error_text, level="error")
        mail_service.send_report(subject=f"❌ {settings.COMPANY_NAME} - Критическая ошибка", body=error_text,
                                 logs=current_logs)
        sys.exit(1)

    finally:
        custom_log("🧹 Выполняется очистка...")
        file_handler.cleanup_temp()

        if session_backup_files:
            custom_log(f"🗑️ Удаление файлов резервных копий ({len(session_backup_files)} шт.)...")
            for b_file in session_backup_files:
                try:
                    if os.path.exists(b_file):
                        os.remove(b_file)
                except Exception:
                    pass

        custom_log("Процесс завершен.")

if __name__ == "__main__":
    current_job = "all"
    if len(sys.argv) > 1:
        current_job = sys.argv[1].lower()

    run_integration(job_type=current_job)