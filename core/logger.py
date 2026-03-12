import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from core.config import settings

# 1. Logger obyektini olamiz
logger = logging.getLogger("sales_integration")
logger.setLevel(settings.LOG_LEVEL)

# 2. ENG MUHIM QISM: Handlerlar oldin qo'shilganligini tekshiramiz.
if not logger.handlers:

    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- A. Konsolga chiqarish (Terminal) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # --- B. Faylga yozish (app.log) ---
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)