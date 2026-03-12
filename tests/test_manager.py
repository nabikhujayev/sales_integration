import unittest
from unittest.mock import patch
import sys
import os
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    import manager
except ImportError:
    sys.path.append(project_root)
    import manager


class TestManager(unittest.TestCase):

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_run_client_success(self, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        client = {"name": "TEST_CLIENT", "env_file": ".env.test", "has_monolit": True}

        # job_type parametri qo'shildi
        manager.run_client(client, "monolit")

        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args

        # main.py endi argument bilan chaqiriladi
        self.assertEqual(args[0], [sys.executable, "main.py", "monolit"])
        self.assertEqual(kwargs['env']['ENV_FILE_PATH'], ".env.test")

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_run_client_file_not_found(self, mock_exists, mock_subprocess):
        mock_exists.return_value = False
        client = {"name": "TEST_CLIENT", "env_file": ".env.missing"}
        manager.run_client(client, "all")
        mock_subprocess.assert_not_called()

    @patch('manager.run_client')
    def test_main_loop_skip_monolit(self, mock_run_client):
        """Monolit yo'q klientlarni sakrab o'tishini tekshirish"""
        original_clients = manager.CLIENTS
        manager.CLIENTS = [
            {"name": "SAYONAR", "env_file": ".env.a", "has_monolit": False},
            {"name": "BORJOMI", "env_file": ".env.b", "has_monolit": True}
        ]

        # Terminaldan "monolit" buyrug'i kelgan deb soxtalashtiramiz
        with patch.object(sys, 'argv', ['manager.py', 'monolit']):
            manager.main()

        # Faqat BORJOMI uchun 1 marta ishlashi kerak (SAYONAR sakrab o'tiladi)
        self.assertEqual(mock_run_client.call_count, 1)
        manager.CLIENTS = original_clients


if __name__ == '__main__':
    unittest.main()