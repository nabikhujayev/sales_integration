import unittest
import os
import shutil
import tempfile
import zipfile
import io
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
grandparent_root = os.path.dirname(project_root)

sys.path.insert(0, grandparent_root)

sys.path.insert(0, project_root)

os.environ["ENV_FILE_PATH"] = os.path.join(project_root, ".env.borjomi")

# --- IMPORT QILISH ---
try:
    from sales_integration.utils.file_handler import FileHandler
except ImportError:
    try:
        from utils.file_handler import FileHandler
    except ImportError as e:
        print("\n❌ XATOLIK: 'file_handler.py' fayli 'utils' papkasida ekanligiga ishonch hosil qiling.")
        raise e


class TestFileHandler(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.handler = FileHandler(base_path=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                pass

    def test_save_zip_to_backup(self):
        """Backup saqlash testi"""
        dummy_content = b"Bu shunchaki test fayli"
        file_path = self.handler.save_zip_to_backup(dummy_content)
        self.assertTrue(os.path.exists(file_path))
        self.assertIn("backups", file_path)
        print("✅ Backup saqlash testi o'tdi.")

    def test_extract_zip_success(self):
        """ZIP faylni ochish va XML larni topish"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test_data.xml', '<root>Data</root>')
            zf.writestr('readme.txt', 'Read me')

        zip_content = zip_buffer.getvalue()
        xml_files = self.handler.extract_zip(zip_content)

        self.assertEqual(len(xml_files), 1)
        self.assertTrue(xml_files[0].endswith('test_data.xml'))
        print("✅ ZIP Extract testi o'tdi.")

    def test_extract_invalid_zip(self):
        """Buzilgan ZIP fayl kelsa"""
        bad_content = b"Men ZIP fayl emasman"
        with self.assertRaises(Exception):
            self.handler.extract_zip(bad_content)
        print("✅ Buzilgan ZIP testi o'tdi.")

    def test_cleanup_temp(self):
        """Temp papkani tozalash"""
        os.makedirs(self.handler.temp_dir, exist_ok=True)
        with open(os.path.join(self.handler.temp_dir, "trash.txt"), 'w') as f:
            f.write("Trash")
        self.handler.cleanup_temp()
        self.assertFalse(os.path.exists(self.handler.temp_dir))
        print("✅ Temp tozalash testi o'tdi.")


if __name__ == '__main__':
    unittest.main()