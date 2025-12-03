"""
Quick test of DrissionPage cookie refresh
First run: Login required (visible browser)
Subsequent runs: Automatic (headless, uses saved session)
"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from auto_refresh_drission import AutoCookieRefresherDrission
    
    print("=" * 60)
    print("DrissionPage Cookie Refresh Test")
    print("=" * 60)
    
    user_data_dir = Path('browser_profile')
    is_first_run = not user_data_dir.exists() or not any(user_data_dir.iterdir())
    
    if is_first_run:
        print("\n[FIRST RUN]")
        print("Browser will open - please login to GMGN.ai")
        print("After login, session will be saved automatically")
        print("Next time, no login needed!")
        headless = False
    else:
        print("\n[SUBSEQUENT RUN]")
        print("Using saved browser session (no login needed!)")
        headless = True
    
    print("\n" + "=" * 60)
    
    refresher = AutoCookieRefresherDrission(
        user_data_dir=user_data_dir,
        headless=headless,
        wait_time=20
    )
    
    try:
        cookies = refresher.get_cookies(login_if_needed=is_first_run)
        
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
                print("\n[OK] Cookies saved to cookies.txt and cookies.json!")
            
            # Update config.py
            if refresher.update_config(cookies):
                print("[OK] Updated config.py with new cookies!")
            else:
                print("[WARNING] Could not update config.py")
            
            if is_first_run:
                print("\n[INFO] Browser session saved!")
                print("Next run will be automatic (no login needed)")
        
        else:
            print("\n[ERROR] Failed to get cookies")
    
    finally:
        if not headless:
            input("\nPress Enter to close browser...")
        refresher.close()

except ImportError as e:
    print(f"[ERROR] {e}")
    print("\nInstall DrissionPage:")
    print("  pip install DrissionPage")

