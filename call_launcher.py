import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('INNOCALLS_API_URL', 'https://platform.innocalls.com/api/v1/call')
BEARER = os.getenv('INNOCALLS_BEARER_TOKEN')
CALL_FLOW_ID = os.getenv('INNOCALLS_CALL_FLOW_ID', 'default_flow')
CONTACTS_PATH = os.getenv('CONTACTS_PATH', 'contacts.xlsx')
DELAY_BETWEEN_CALLS = int(os.getenv('DELAY_BETWEEN_CALLS', 5))  # ثواني بين المكالمات

headers = {'Authorization': f'Bearer {BEARER}'}

def call_customer(phone):
    payload = {"phone": phone, "call_flow_id": CALL_FLOW_ID, "message": "مرحبا! هذا اختبار."}
    retries = 2
    for attempt in range(retries + 1):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                print(f"[SUCCESS] Call initiated to {phone}")
                return "Calling"
            else:
                print(f"[WARNING] Call to {phone} returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[ERROR] Call error to {phone}: {e}")
        if attempt < retries:
            print(f"Retrying {phone} ({attempt + 1}/{retries})...")
            time.sleep(2)
    return "Failed"

def call_customers():
    df = pd.read_excel(CONTACTS_PATH)
    if 'Status' not in df.columns:
        df['Status'] = ""
    
    for idx, row in df.iterrows():
        phone = row['Phone']
        print(f"\nCalling {phone}...")
        status = call_customer(phone)
        df.loc[idx, 'Status'] = status
        time.sleep(DELAY_BETWEEN_CALLS)
    
    # حفظ Excel مرة واحدة بعد كل المكالمات
    df.to_excel(CONTACTS_PATH, index=False)
    print("\nAll calls processed. Status updated in Excel.")

if __name__ == '__main__':
    call_customers()
