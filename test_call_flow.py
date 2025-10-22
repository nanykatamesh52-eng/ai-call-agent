import requests
WEBHOOK_URL = 'http://localhost:8000/webhook'
def test_call(speech_text, call_id='demo-call-001', phone='+2010000001'):
    payload = {'callId': call_id, 'phone': phone, 'speech_text': speech_text}
    print('Sending test payload:', payload)
    resp = requests.post(WEBHOOK_URL, json=payload)
    print('Status', resp.status_code)
    try:
        print(resp.json())
    except:
        print(resp.text)
if __name__ == '__main__':
    test_call('الأسعار كام؟')
    test_call('فين مكانكم؟')
    test_call('شكراً مش مهتم')
