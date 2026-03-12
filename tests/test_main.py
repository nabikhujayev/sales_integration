import unittest
from unittest.mock import patch
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ["ENV_FILE_PATH"] = os.path.join(project_root, ".env.borjomi")

try:
    from main import run_integration
except ImportError:
    sys.path.append(project_root)
    from main import run_integration

class TestMainIntegration(unittest.TestCase):

    @patch('main.settings')
    @patch('main.smartup_client')
    @patch('main.file_handler')
    @patch('main.sftp_manager')
    @patch('main.ftp_manager')
    @patch('main.mail_service')
    @patch('main.xml_transformer')
    @patch('main.baltika_client') # YANGI API CLIENT MOCK
    def test_run_integration_saleswork(self, mock_baltika, mock_transformer, mock_mail, mock_ftp, mock_sftp, mock_file_handler, mock_smartup, mock_settings):
        """Faqat Saleswork ishlaganda (SFTP ga ketadi)"""
        mock_settings.COMPANY_NAME = "TestCompany"
        mock_settings.get_template_ids = [902]
        mock_settings.ENABLE_MONOLIT_REPORT = False
        mock_settings.PROTOCOL = "SFTP"

        mock_smartup.download_sales_report.return_value = b"zip_bytes"
        mock_file_handler.extract_zip.return_value = ["outlets.xml"]
        mock_transformer.process_outlets.return_value = True
        mock_sftp.upload_files.return_value = True

        with patch('os.remove'), patch('os.path.exists', return_value=True):
            run_integration("saleswork")

        # SFTP ishlashi kerak, Baltika API ishlamasligi kerak
        mock_sftp.upload_files.assert_called_once()
        mock_baltika.send_xml.assert_not_called()
        mock_mail.send_report.assert_called()

    @patch('main.settings')
    @patch('main.smartup_client')
    @patch('main.file_handler')
    @patch('main.sftp_manager')
    @patch('main.mail_service')
    @patch('main.baltika_client')
    def test_run_integration_monolit(self, mock_baltika, mock_mail, mock_sftp, mock_file_handler, mock_smartup, mock_settings):
        """Faqat Monolit ishlaganda (API ga ketadi)"""
        mock_settings.COMPANY_NAME = "TestCompany"
        mock_settings.get_template_ids = []
        mock_settings.ENABLE_MONOLIT_REPORT = True
        mock_settings.get_monolit_report_types = ["$export_balance"]

        mock_smartup.download_monolit_report.return_value = b"<xml>data</xml>"
        mock_file_handler.save_monolit_to_backup.return_value = "/tmp/backup.xml"
        mock_baltika.send_xml.return_value = True

        with patch('os.remove'), patch('os.path.exists', return_value=True):
            run_integration("monolit")

        # Baltika API ishlashi kerak, SFTP ishlamasligi kerak!
        mock_baltika.send_xml.assert_called_once()
        mock_sftp.upload_files.assert_not_called()
        mock_mail.send_report.assert_called()

if __name__ == '__main__':
    unittest.main()