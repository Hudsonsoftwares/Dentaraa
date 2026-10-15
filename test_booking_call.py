import requests
import re
import json

s = requests.Session()
r_page = s.get('http://127.0.0.1:8069/?db=DenBell')

# Search for csrf_token
m = re.search(r'"csrf_token":\s*"([^"]+)"', r_page.text)
csrf = m.group(1) if m else ''
if not csrf:
    m2 = re.search(r'name="csrf_token"\s+value="([^"]+)"', r_page.text)
    csrf = m2.group(1) if m2 else ''

print('CSRF token found:', csrf[:15] if csrf else 'None')

payload = {
    'csrf_token': csrf,
    'patient_type': 'new',
    'name': 'Duplicate Attempter',
    'phone': '9876543200',
    'email': 'dup@example.com',
    'appointment_type_id': '2',
    'doctor_id': '1', # Dr. Devipriya who is already booked at 11:00 on 2026-10-25!
    'appointment_date': '2026-10-25',
    'appointment_time': '11:00',
    'notes': 'Trying to double book'
}

r = s.post('http://127.0.0.1:8069/website/action/book_appointment', data=payload)
print('Status:', r.status_code)
print('JSON Response:', r.json())
