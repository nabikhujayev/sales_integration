import unittest
from unittest.mock import patch, Mock
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ["ENV_FILE_PATH"] = os.path.join(project_root, ".env.borjomi")

from services.baltika_client import BaltikaClient  # noqa: E402


class TestBaltikaClient(unittest.TestCase):

    def setUp(self):
        self.client = BaltikaClient()
        self.client.url = "http://fake-baltika-api.com"

    @patch('requests.post')
    def test_send_xml_success(self, mock_post):
        """Baltika API ga XML muvaffaqiyatli ketishini tekshirish"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success Answer"
        mock_post.return_value = mock_response

        xml_data = b"<Root>Data</Root>"
        result = self.client.send_xml(xml_data, "Test_Report")

        self.assertTrue(result)
        mock_post.assert_called_once()

        # XMLData parametridan yuborilganligini tekshirish
        kwargs = mock_post.call_args[1]
        self.assertEqual(kwargs['data']['XMLData'], "<Root>Data</Root>")

    @patch('requests.post')
    def test_send_xml_failure(self, mock_post):
        """API xato qaytarsa (masalan 500 Error)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = self.client.send_xml(b"Data", "Test_Report")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()