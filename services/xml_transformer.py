import os
import json
import xml.etree.ElementTree as ET
from core.logger import logger


class XMLTransformer:
    """
    XML fayllarni biznes qoidalar asosida o'zgartiruvchi servis.
    Hozirda faqat AREA_ID larni almashtirish uchun moslashtirilgan.
    """

    def __init__(self, mapping_file: str = "data/area_mappings.json"):
        self.mapping_file = mapping_file
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> dict:
        """JSON fayldan ID lar lug'atini yuklaydi."""
        if not os.path.exists(self.mapping_file):
            logger.warning(f"Файл маппинга не найден: {self.mapping_file}")
            return {}

        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Маппинг загружен: {len(data)} правил.")
                return data
        except Exception as e:
            logger.error(f"Ошибка при чтении файла маппинга: {e}")
            return {}

    def process_outlets(self, file_path: str) -> bool:
        if not self.mappings:
            return False

        try:
            logger.info(f"Анализ Outlets.xml: {file_path}")

            # XML ni o'qish
            tree = ET.parse(file_path)
            root = tree.getroot()

            changes_count = 0

            for elem in root.iter():
                current_id = elem.get('AREA_ID')
                if current_id and current_id in self.mappings:
                    new_id = self.mappings[current_id]
                    elem.set('AREA_ID', new_id)
                    changes_count += 1

            if changes_count > 0:
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
                logger.info(f"✅ Успешно заменено {changes_count} AREA_ID.")
                return True
            else:
                logger.info("ℹ️ AREA_ID для замены не найдены.")
                return False

        except ET.ParseError:
            logger.error("Ошибка чтения XML-файла (поврежденный формат).")
            return False
        except Exception as e:
            logger.error(f"Ошибка трансформации XML: {e}")
            return False


# Singleton
xml_transformer = XMLTransformer()