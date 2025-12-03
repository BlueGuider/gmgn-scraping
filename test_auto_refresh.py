"""
Quick test of automated cookie refresh
"""
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        # Fallback for older Python
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from auto_refresh_cookies import AutoCookieRefresher
    
    print("Testing automated cookie refresh...")
    print("=" * 60)
    
    # Test with visible browser first (to see what happens)
    print("\n[INFO] Starting browser (visible mode for testing)...")
    refresher = AutoCookieRefresher(headless=False, wait_time=20)
    
    try:
        cookies = refresher.get_cookies()
        
        if cookies:
            print(f"\n[SUCCESS] Got {len(cookies)} cookies")
            print("\nCookies:")
            for key in cookies.keys():
                print(f"  - {key}")
            
            # Check critical cookies
            critical = ['cf_clearance', '__cf_bm', 'sid']
            missing = [c for c in critical if c not in cookies]
            if missing:
                print(f"\n[WARNING] Missing: {', '.join(missing)}")
            else:
                print("\n[OK] All critical cookies present!")
            
            # Save cookies
            if refresher.save_cookies(cookies):
                print("\n[OK] Cookies saved!")
            
        else:
            print("\n[ERROR] Failed to get cookies")
    
    finally:
        input("\nPress Enter to close browser...")
        refresher.close()

except ImportError as e:
    print(f"[ERROR] {e}")
    print("\nInstall dependencies:")
    print("  pip install selenium webdriver-manager")

