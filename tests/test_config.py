import unittest
import sys
import os

# --- 1. YO'LNI TO'G'IRLASH (Path Fix) ---
# Hozirgi fayl (test_config.py) turgan joy
current_dir = os.path.dirname(os.path.abspath(__file__))
# Bir qavat yuqoriga chiqamiz (Loyiha asosiy papkasi: sales_integration)
project_root = os.path.dirname(current_dir)
# Loyiha papkasini Python qidiruv yo'lining ENG BOSHIGA qo'shamiz
sys.path.insert(0, project_root)

# --- 2. ENV FAYLNI TANITISH (Import xatosini oldini olish) ---
# config.py import bo'lganda darhol .env o'qishga harakat qiladi.
# Unga aniq yo'lni ko'rsatmasak, test papkasi ichidan qidirib, topolmay xato beradi.
# Biz shunchaki mavjud fayllardan birini ko'rsatib turamiz (test uchun buning ahamiyati yo'q,
# chunki biz pastda 'dummy_data' bilan baribir ustidan yozib yuboramiz).
os.environ["ENV_FILE_PATH"] = os.path.join(project_root, ".env.borjomi")

# Endi bemalol import qilamiz
from core.config import Settings  # noqa: E402

class TestConfig(unittest.TestCase):
    """
    Config faylidagi mantiqiy funksiyalarni tekshirish uchun testlar.
    """

    def setUp(self):
        """
        Test uchun soxta ma'lumotlar.
        """
        self.dummy_data = {
            "COMPANY_NAME": "TestCompany",
            "SMARTUP_SERVER_URL": "http://test.com",
            "SMARTUP_CLIENT_ID": "123",
            "SMARTUP_CLIENT_SECRET": "secret",
            "COMPANY_ID": 1,
            "FILIAL_ID": 1,
            "TEMPLATE_ID": "100",
            "SFTP_SERVER": "sftp.test",
            "SFTP_PORT": 22,
            "SFTP_USERNAME": "user",
            "SFTP_PASSWORD": "pass",
            "SFTP_REMOTE_PATH": "/",
            "EMAIL_SENDER": "sender@test.com",
            "EMAIL_PASSWORD": "pass",
            "EMAIL_RECIPIENTS": "test@test.com",
            "SMTP_SERVER": "smtp.test",
            "SMTP_PORT": 587,
            "ENABLE_XML_TRANSFORMATION": False
        }

    def test_recipient_list_clean(self):
        """Email ro'yxatini tozalashni tekshirish"""
        data = self.dummy_data.copy()
        data["EMAIL_RECIPIENTS"] = " ali@gmail.com, vali@mail.ru , gani@yandex.uz "
        settings = Settings(**data)
        expected = ["ali@gmail.com", "vali@mail.ru", "gani@yandex.uz"]
        self.assertEqual(settings.recipient_list, expected)

    def test_template_ids_normal(self):
        """Ko'p shablon ID larini tekshirish"""
        data = self.dummy_data.copy()
        data["TEMPLATE_ID"] = "3301, 3302"
        settings = Settings(**data)
        self.assertEqual(settings.get_template_ids, [3301, 3302])

    def test_template_ids_single(self):
        """Bitta shablon ID sini tekshirish"""
        data = self.dummy_data.copy()
        data["TEMPLATE_ID"] = "902"
        settings = Settings(**data)
        self.assertEqual(settings.get_template_ids, [902])

    def test_template_ids_invalid(self):
        """Xato yozilgan ID larni tekshirish"""
        data = self.dummy_data.copy()
        data["TEMPLATE_ID"] = "101, salom, 102"
        settings = Settings(**data)
        self.assertEqual(settings.get_template_ids, [])

    def test_template_ids_empty(self):
        """Bo'sh ID ni tekshirish"""
        data = self.dummy_data.copy()
        data["TEMPLATE_ID"] = ""
        settings = Settings(**data)
        self.assertEqual(settings.get_template_ids, [])

if __name__ == '__main__':
    unittest.main(verbosity=2)