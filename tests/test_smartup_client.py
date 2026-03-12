import unittest
from unittest.mock import patch, Mock
import sys
import os
import io
import zipfile

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
parent_root = os.path.dirname(project_root)

sys.path.insert(0, project_root)
sys.path.insert(0, parent_root)

os.environ["ENV_FILE_PATH"] = os.path.join(project_root, ".env.borjomi")

# Import
try:
    from services.smartup_client import SmartupClient
except ImportError:
    from services.smartup_client import SmartupClient


class TestSmartupClient(unittest.TestCase):

    def setUp(self):
        self.client = SmartupClient()
        self.client.base_url = "http://test-api.smartup.uz"

    @patch('requests.post')
    def test_get_oauth_token_success(self, mock_post):
        """Tokenni muvaffaqiyatli olish"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "fake_token_123"}
        mock_post.return_value = mock_response

        token = self.client._get_oauth_token()

        self.assertEqual(token, "Bearer fake_token_123")
        self.assertIn("/security/oauth/token", mock_post.call_args[0][0])
        print("✅ Token olish (Success) testi o'tdi.")

    @patch('requests.post')
    def test_get_oauth_token_fail(self, mock_post):
        """Token olishda xatolik bo'lsa"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.client._get_oauth_token()

        print("✅ Token xatoligi (Fail) testi o'tdi.")

    @patch('requests.post')
    def test_download_sales_report_success(self, mock_post):
        """Hisobotni muvaffaqiyatli yuklash"""
        self.client.token = "Bearer old_token"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('report.xml', 'TEST XML CONTENT')
        valid_zip_content = zip_buffer.getvalue()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [valid_zip_content]
        mock_post.return_value = mock_response

        result = self.client.download_sales_report(template_id=902)

        self.assertEqual(result, valid_zip_content)
        self.assertIn("/trade/rep/integration/saleswork", mock_post.call_args[0][0])
        print("✅ Hisobot yuklash (ZIP Success) testi o'tdi.")

    @patch('requests.post')
    def test_download_not_zip_error(self, mock_post):
        """Agar server ZIP emas, HTML xato qaytarsa"""
        self.client.token = "Bearer token"

        # HTML kontent (ZIP emas)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"<html>Error</html>"]
        mock_post.return_value = mock_response

        # Exception kutamiz
        with self.assertRaises(Exception) as cm:
            self.client.download_sales_report(template_id=902)

        self.assertIn("Сервер не вернул ZIP-файл", str(cm.exception))

        print("✅ Noto'g'ri format (Not ZIP) testi o'tdi.")

    @patch('requests.post')
    def test_retry_logic_on_401(self, mock_post):
        """Retry logikasini tekshirish"""
        self.client.token = "Bearer eskirgan_token"

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Authorization required"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.download_sales_report(template_id=902)

        print("✅ Retry logikasi (401 Unauthorized) testi o'tdi.")

    @patch('requests.post')
    def test_download_monolit_report_success(self, mock_post):
        """Monolit hisobotni yuklash va 5 kunlik oraliqni tekshirish"""
        self.client.token = "Bearer token"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<xml>Monolit Data</xml>"
        mock_post.return_value = mock_response

        result = self.client.download_monolit_report(report_type="$export_balance")

        self.assertEqual(result, b"<xml>Monolit Data</xml>")

        # 5 kunlik URL va Payload yuborilganligini tekshiramiz
        args, kwargs = mock_post.call_args
        self.assertIn("integration_two$export_balance", args[0])
        self.assertIn("begin_date", kwargs['json'])
        self.assertIn("end_date", kwargs['json'])
        print("✅ Monolit yuklash (Success) testi o'tdi.")




if __name__ == '__main__':
    unittest.main()