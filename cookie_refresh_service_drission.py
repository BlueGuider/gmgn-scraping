"""
Background service to automatically refresh cookies using DrissionPage
Run this as a background service - login once, then it's automatic!
"""
import sys
import io
import time
import schedule
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from auto_refresh_drission import AutoCookieRefresherDrission
from check_cookies import check_cookies


def refresh_cookies_job():
    """Job to refresh cookies"""
    print(f"\n[{datetime.now()}] Starting cookie refresh...")
    
    user_data_dir = Path('browser_profile')
    is_first_run = not user_data_dir.exists() or not any(user_data_dir.iterdir())
    
    # Use headless after first run (when session is saved)
    refresher = AutoCookieRefresherDrission(
        user_data_dir=user_data_dir,
        headless=not is_first_run,  # Visible on first run for login
        wait_time=20
    )
    
    try:
        cookies = refresher.get_cookies(login_if_needed=is_first_run)
        
        if cookies:
            refresher.save_cookies(cookies)
            refresher.update_config(cookies)
            
            # Verify cookies work
            print("Verifying cookies...")
            if check_cookies():
                print(f"[{datetime.now()}] [SUCCESS] Cookies refreshed and verified!")
            else:
                print(f"[{datetime.now()}] [WARNING] Cookies refreshed but verification failed")
        else:
            print(f"[{datetime.now()}] [ERROR] Failed to refresh cookies")
    
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Exception during refresh: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        refresher.close()


def main():
    """Run cookie refresh service"""
    print("=" * 60)
    print("GMGN Cookie Refresh Service (DrissionPage)")
    print("=" * 60)
    print("\nThis service will automatically refresh cookies:")
    print("- Every 2 hours (recommended)")
    print("- Uses saved browser session (login once!)")
    print("- No manual login needed after first time")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Check if first run
    user_data_dir = Path('browser_profile')
    is_first_run = not user_data_dir.exists() or not any(user_data_dir.iterdir())
    
    if is_first_run:
        print("\n[IMPORTANT] First run detected!")
        print("You'll need to login once in the browser window")
        print("After that, login will be saved and reused automatically")
        input("\nPress Enter to start (browser will open for login)...")
    
    # Schedule refresh every 2 hours
    schedule.every(2).hours.do(refresh_cookies_job)
    
    # Also refresh immediately
    print("\nRunning initial refresh...")
    refresh_cookies_job()
    
    # Keep running
    print("\nService running. Refreshing every 2 hours...")
    print("(Browser will be headless after first login)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nService stopped.")


if __name__ == "__main__":
    main()








