"""
Helper script to fix browser profile issues
Run this if you get connection errors
"""
import sys
import io
from pathlib import Path
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def main():
    print("=" * 60)
    print("Browser Profile Fixer")
    print("=" * 60)
    
    browser_profile = Path('browser_profile')
    
    if browser_profile.exists():
        print(f"\nFound browser profile at: {browser_profile}")
        print("\nOptions:")
        print("1. Delete profile (will need to login again)")
        print("2. Keep profile (try to fix connection)")
        print("3. Exit")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            try:
                shutil.rmtree(browser_profile)
                print("\n[OK] Browser profile deleted")
                print("Next run will create a fresh profile (login required)")
            except Exception as e:
                print(f"\n[ERROR] Failed to delete: {e}")
        elif choice == '2':
            print("\n[INFO] Keeping profile")
            print("Make sure:")
            print("1. All Chrome/Chromium browsers are closed")
            print("2. No other scripts are using the profile")
            print("3. Try running again")
        else:
            print("\nExiting...")
    else:
        print("\n[INFO] No browser profile found")
        print("This is normal for first run")

if __name__ == "__main__":
    main()








