import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3NzU5Nzc1LCJpYXQiOjE3Njc3NTk0NzUsImp0aSI6ImU5MmY2YTEwMDZlOTQ5Y2FhMGYxNjUxNTNkMDkzMmRlIiwidXNlcl9pZCI6IjEifQ.11x4RP1GPGw4sO05n-oKyBG6_al1o4E-K2zKa7qhAgo"
SESSION_ID = 17   # replace with real session id

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "question_code": "PHQ9_Q1",
    "value": 3
}

r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{SESSION_ID}/events/",
    headers=headers,
    json=payload,
)

print("Status:", r.status_code)
print("Response:", r.text)
