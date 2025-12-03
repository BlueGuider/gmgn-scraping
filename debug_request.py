"""
Debug script to see what's being sent in requests
"""
import requests
from cookie_helper import parse_cookie_string

# Load cookies
with open('cookies.txt', 'r') as f:
    cookie_string = f.read().strip()

cookies = parse_cookie_string(cookie_string)

# Create session
session = requests.Session()

# Set headers
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Referer': 'https://gmgn.ai/',
    'Origin': 'https://gmgn.ai',
})

# Set cookies
for key, value in cookies.items():
    session.cookies.set(key, value, domain='.gmgn.ai')

print("Cookies loaded:")
for name, value in session.cookies.items():
    print(f"  {name}: {value[:50]}...")

# Test request
url = "https://gmgn.ai/defi/quotation/v1/rank/bsc/wallets/7d"
params = {
    'device_id': 'test-device-id',
    'fp_did': 'test-fp-did',
    'client_id': 'gmgn_web_20251201-8195-937e742',
    'from_app': 'gmgn',
    'app_ver': '20251201-8195-937e742',
    'tz_name': 'Europe/London',
    'tz_offset': 0,
    'app_lang': 'en-US',
    'os': 'web',
    'worker': 0,
    'orderby': 'pnl_7d',
    'direction': 'desc'
}

print("\nMaking request...")
print(f"URL: {url}")
print(f"Cookies being sent: {len(session.cookies)} cookies")

response = session.get(url, params=params, timeout=30)

print(f"\nStatus Code: {response.status_code}")
print(f"Response Headers:")
for key, value in response.headers.items():
    if key.lower() in ['set-cookie', 'cf-ray', 'cf-cache-status']:
        print(f"  {key}: {value}")

if response.status_code == 403:
    print("\n[ERROR] Still getting 403. Possible reasons:")
    print("1. Cookies expired - get fresh cookies from browser")
    print("2. Cloudflare challenge not passed - visit gmgn.ai in browser first")
    print("3. IP/User-Agent fingerprint mismatch")
    print("4. Missing required headers")
    
    # Check response body
    if response.text:
        print(f"\nResponse body (first 500 chars):")
        print(response.text[:500])
elif response.status_code == 200:
    print("\n[SUCCESS] Request worked!")
    try:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
    except:
        print("Response is not JSON")



