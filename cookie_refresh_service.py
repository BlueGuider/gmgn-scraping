"""
Background service to automatically refresh cookies
Run this as a background service or scheduled task
"""
import sys
import io
import time
import schedule
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        # Fallback for older Python
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from auto_refresh_cookies import AutoCookieRefresher
from check_cookies import check_cookies


def refresh_cookies_job():
    """Job to refresh cookies"""
    print(f"\n[{datetime.now()}] Starting cookie refresh...")
    
    refresher = AutoCookieRefresher(headless=True, wait_time=20)
    
    try:
        cookies = refresher.get_cookies()
        
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
    
    finally:
        refresher.close()


def main():
    """Run cookie refresh service"""
    print("=" * 60)
    print("GMGN Cookie Refresh Service")
    print("=" * 60)
    print("\nThis service will automatically refresh cookies:")
    print("- Every 2 hours (recommended)")
    print("- Before cookies expire")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Schedule refresh every 2 hours
    schedule.every(2).hours.do(refresh_cookies_job)
    
    # Also refresh immediately
    print("\nRunning initial refresh...")
    refresh_cookies_job()
    
    # Keep running
    print("\nService running. Refreshing every 2 hours...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nService stopped.")


if __name__ == "__main__":
    main()

