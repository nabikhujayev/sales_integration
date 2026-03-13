import requests
from datetime import datetime

# ==================== O'ZINGIZNING PAROLLARNI YOZING ====================
BASE_URL = "https://smartup.online"  # Masalan: "https://smartup.online"
CLIENT_ID = "E2D189D7BA0952EA6AFCA1C11BF87BE3"
CLIENT_SECRET = "80E450470A7E6AC289E529A4D73C21AF02440D3CC42FB13C76F887B4396EDB54B449057C255A5E172C9FD6741BD190354C572CF7AE15E227577183299D89FF93"


# =======================================================================

def run_test():
    print("=== ТЕСТИРОВАНИЕ API (BEZ CONFIG) ===")

    # 1. TOKEN OLISH
    print("🔑 Получение токена...")
    token_url = f"{BASE_URL}/security/oauth/token"
    token_payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "read"
    }

    try:
        token_resp = requests.post(token_url, json=token_payload, timeout=10)
        token_resp.raise_for_status()
        token = f"Bearer {token_resp.json()['access_token']}"
        print("✅ Токен успешно получен!\n")
    except Exception as e:
        print(f"❌ Ошибка токена: {e}")
        return

    # =====================================================================
    # 2. URL MANZILNI SHU YERDA O'ZGARTIRIB TEST QILAMIZ
    # =====================================================================
    report_type = "export_deal_and_input_together"

    # VARIANT 1: $ belgisi bilan
    # url = f"{BASE_URL}/trade/rep/integration/integration_two${report_type}"

    # VARIANT 2: : (ikki nuqta) bilan
    # url = f"{BASE_URL}/trade/rep/integration/integration_two:{report_type}"

    # VARIANT 3: /b/ bilan
    url = f"{BASE_URL}/b/trade/rep/integration/integration_two:{report_type}"
    # =====================================================================

    today = datetime.today().strftime('%d.%m.%Y')
    payload = {
        "begin_date": today,
        "end_date": today,
        "filial_id": []
    }

    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    print(f"📤 URL: {url}")
    print(f"📦 Payload: {payload}")
    print("⏳ Отправка запроса (подождите)...\n")

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        print(f"📥 СТАТУС КОД: {resp.status_code}")

        if resp.status_code == 200:
            print("🎉 УРА! РАБОТАЕТ! (200 OK)")
            print(f"Размер файла: {len(resp.content)} байт")
            print("Начало ответа:")
            print(resp.text[:300])
        else:
            print(f"❌ ОШИБКА (Статус {resp.status_code}):")
            print(resp.text)

    except Exception as e:
        print(f"❌ Критическая ошибка при запросе: {e}")


if __name__ == "__main__":
    run_test()