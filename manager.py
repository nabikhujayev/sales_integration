import subprocess
import os
import sys
from datetime import datetime

# Klientlar ro'yxatiga 'has_monolit' degan kalit qo'shdik.
# Bu 20:00 da qaysi klientni ishga tushirishni va qaysini sakrab o'tishni hal qiladi.

CLIENTS = [
    {"name": "SAYONAR", "env_file": ".env.sayonar", "has_monolit": False},
    {"name": "BORJOMI", "env_file": ".env.borjomi", "has_monolit": True},
    {"name": "ROYALSTAR", "env_file": ".env.royalstar", "has_monolit": False},
]


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [MANAGER] {message}")


def run_client(client, job_type):
    name = client["name"]
    env_file = client["env_file"]

    if not os.path.exists(env_file):
        log(f"❌ ОШИБКА: Файл {env_file} для {name} не найден!")
        return

    log(f"🚀 Запуск процесса {name} (Режим: {job_type.upper()})... (Config: {env_file})")

    # Hozirgi muhit o'zgaruvchilarini nusxalab olamiz
    env = os.environ.copy()
    # Biz config.py ga qaysi faylni o'qish kerakligini aytamiz
    env["ENV_FILE_PATH"] = env_file

    try:
        # ASOSIY O'ZGARISH: main.py ga job_type ni yuboramiz (masalan: main.py saleswork)
        result = subprocess.run(
            [sys.executable, "main.py", job_type],
            env=env,
            check=True,
            text=True
        )
        log(f"✅ Процесс {name} успешно завершен.")
    except subprocess.CalledProcessError as e:
        log(f"⚠️ Ошибка в процессе {name}. Cod: {e.returncode}")
    except Exception as e:
        log(f"❌ {name} не запустился: {e}")


def main():
    # Terminaldan kelgan buyruqni o'qiymiz (saleswork, monolit yoki all)
    job_type = "all"
    if len(sys.argv) > 1:
        job_type = sys.argv[1].lower()
    log(f"=== ЗАПУСК ИНТЕГРАЦИИ ({job_type.upper()}) ===")

    for client in CLIENTS:
        # Agar buyruq 'monolit' bo'lsa, lekin klientda monolit yo'q bo'lsa (SAYONAR, ROYALSTAR)
        # uni sakrab o'tamiz, vaqtni tejaymiz!
        if job_type == "monolit" and not client.get("has_monolit"):
            log(f"⏭️ Пропуск {client['name']} (не имеет Monolit отчетов)")
            continue

        run_client(client, job_type)
        log("-" * 40)

    log("=== ВСЕ ЗАДАЧИ ЗАВЕРШЕНЫ ===")

if __name__ == "__main__":
    main()