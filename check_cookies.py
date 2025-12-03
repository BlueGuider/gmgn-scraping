"""
Check if current cookies are still valid
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from gmgn_client import GMGNClient
from cookie_helper import parse_cookie_string
import os

def check_cookies():
    print("Checking cookie validity...")
    print("=" * 60)
    
    # Load cookies
    cookies = None
    device_id = None
    fp_did = None
    
    # Try from cookies.txt
    if os.path.exists('cookies.txt'):
        with open('cookies.txt', 'r') as f:
            cookie_string = f.read().strip()
            if cookie_string:
                cookies = parse_cookie_string(cookie_string)
                print("[OK] Loaded cookies from cookies.txt")
    
    # Try from config.py
    if not cookies:
        try:
            from config import COOKIES, DEVICE_ID, FP_DID
            cookies = COOKIES
            device_id = DEVICE_ID
            fp_did = FP_DID
            if cookies:
                print("[OK] Loaded cookies from config.py")
        except (ImportError, AttributeError):
            pass
    
    if not cookies:
        print("[ERROR] No cookies found!")
        print("Run refresh_cookies.py to add cookies")
        return False
    
    # Check for critical cookies
    critical = ['cf_clearance', '__cf_bm', 'sid']
    missing = [c for c in critical if c not in cookies]
    if missing:
        print(f"[WARNING] Missing cookies: {', '.join(missing)}")
    
    # Test with API request
    print("\nTesting API request...")
    client = GMGNClient(cookies=cookies, device_id=device_id, fp_did=fp_did)
    
    result = client.get_most_profitable_wallets("7d")
    
    if 'error' in result:
        print(f"[FAILED] Cookies are invalid or expired")
        print(f"Error: {result['error']}")
        if '403' in str(result.get('status_code', '')):
            print("\n[ACTION REQUIRED] Refresh cookies using refresh_cookies.py")
        return False
    elif 'data' in result and 'rank' in result.get('data', {}):
        rank = result['data']['rank']
        print(f"[SUCCESS] Cookies are valid!")
        print(f"Got {len(rank)} wallets")
        return True
    else:
        print("[WARNING] Unexpected response format")
        return False

if __name__ == "__main__":
    is_valid = check_cookies()
    sys.exit(0 if is_valid else 1)








