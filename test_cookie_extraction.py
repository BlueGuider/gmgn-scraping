"""
Test script to see ALL cookies in browser
Run this to debug cookie extraction
"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    import time
    
    print("=" * 60)
    print("Cookie Extraction Test")
    print("=" * 60)
    
    # Setup browser
    options = ChromiumOptions()
    user_data_dir = Path('browser_profile')
    if user_data_dir.exists():
        options.set_user_data_path(str(user_data_dir.absolute()))
        print("[OK] Using saved browser session")
    else:
        print("[INFO] First run - will need to login")
    
    options.headless(False)  # Visible to see what's happening
    
    page = ChromiumPage(addr_or_opts=options)
    
    print("\nVisiting GMGN.ai...")
    page.get('https://gmgn.ai/')
    
    print("\nWaiting 30 seconds for Cloudflare and page load...")
    print("(Watch the browser - make sure you're logged in)")
    time.sleep(30)
    
    # Navigate to trade page
    print("\nNavigating to trade page...")
    page.get('https://gmgn.ai/trade/iMPLjKQt?chain=bsc')
    time.sleep(5)
    
    print("\n" + "=" * 60)
    print("Extracting cookies using all methods...")
    print("=" * 60)
    
    all_cookies = {}
    
    # Method 1: CDP getAllCookies
    print("\n[Method 1] CDP getAllCookies (all domains):")
    try:
        browser = page.browser
        cookies_cdp = browser.run_cdp('Network.getAllCookies')
        if cookies_cdp and 'cookies' in cookies_cdp:
            print(f"  Total cookies in browser: {len(cookies_cdp['cookies'])}")
            for cookie in cookies_cdp['cookies']:
                domain = cookie.get('domain', '')
                name = cookie.get('name')
                if 'gmgn.ai' in domain or domain == '':
                    all_cookies[name] = cookie.get('value')
                    print(f"  - {name} (domain: {domain})")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Method 2: DrissionPage cookies()
    print("\n[Method 2] DrissionPage cookies():")
    try:
        cookies_dp = page.cookies()
        print(f"  Cookies from page: {len(cookies_dp) if cookies_dp else 0}")
        if cookies_dp:
            for cookie in cookies_dp:
                name = cookie.get('name') if isinstance(cookie, dict) else (cookie.name if hasattr(cookie, 'name') else None)
                value = cookie.get('value') if isinstance(cookie, dict) else (cookie.value if hasattr(cookie, 'value') else None)
                if name:
                    all_cookies[name] = value
                    print(f"  - {name}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Method 3: JavaScript
    print("\n[Method 3] JavaScript document.cookie:")
    try:
        js_cookies = page.run_js('return document.cookie')
        print(f"  Cookie string: {js_cookies[:100]}...")
        if js_cookies:
            from cookie_helper import parse_cookie_string
            parsed = parse_cookie_string(js_cookies)
            for name, value in parsed.items():
                all_cookies[name] = value
                print(f"  - {name}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total unique cookies found: {len(all_cookies)}")
    print(f"Cookie names: {', '.join(sorted(all_cookies.keys()))}")
    
    # Check critical cookies
    critical = ['cf_clearance', '__cf_bm', 'sid']
    print("\nCritical cookies:")
    for name in critical:
        if name in all_cookies:
            print(f"  ✓ {name}: {all_cookies[name][:50]}...")
        else:
            print(f"  ✗ {name}: MISSING")
    
    if 'cf_clearance' not in all_cookies or 'sid' not in all_cookies:
        print("\n[WARNING] Missing critical cookies!")
        print("Possible reasons:")
        print("1. Cloudflare challenge didn't complete")
        print("2. Not logged into GMGN.ai")
        print("3. Need to wait longer")
        print("4. Cookies set on different domain")
    
    input("\nPress Enter to close browser...")
    page.quit()
    
except ImportError:
    print("[ERROR] DrissionPage not installed")
    print("Install with: pip install DrissionPage")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()








