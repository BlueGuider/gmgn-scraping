"""
Script to help refresh cookies from browser
Run this when you need to update cookies
"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from cookie_helper import parse_cookie_string
import json

def main():
    print("=" * 60)
    print("GMGN Cookie Refresh Helper")
    print("=" * 60)
    print("\nSteps:")
    print("1. Open GMGN.ai in your browser")
    print("2. Press F12 > Network tab")
    print("3. Make a request (click something)")
    print("4. Find a request to gmgn.ai")
    print("5. Copy the Cookie header value")
    print("\n" + "=" * 60)
    
    cookie_string = input("\nPaste your cookie string here: ").strip()
    
    if not cookie_string:
        print("[ERROR] No cookie string provided")
        return
    
    try:
        cookies = parse_cookie_string(cookie_string)
        
        print(f"\n[OK] Parsed {len(cookies)} cookies")
        print("\nCookies found:")
        for key in cookies.keys():
            print(f"  - {key}")
        
        # Check for critical cookies
        critical = ['cf_clearance', '__cf_bm', 'sid']
        missing = [c for c in critical if c not in cookies]
        if missing:
            print(f"\n[WARNING] Missing critical cookies: {', '.join(missing)}")
        else:
            print("\n[OK] All critical cookies present!")
        
        # Save to cookies.txt
        with open('cookies.txt', 'w') as f:
            f.write(cookie_string)
        print("\n[SAVED] Updated cookies.txt")
        
        # Generate config.py format
        print("\n" + "=" * 60)
        print("Add this to config.py:")
        print("=" * 60)
        print("\nCOOKIES = {")
        for key, value in cookies.items():
            # Truncate very long values for display
            display_value = value[:80] + "..." if len(value) > 80 else value
            print(f"    '{key}': '{display_value}',")
        print("}")
        
        # Also save as JSON for reference
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print("\n[SAVED] Also saved to cookies.json (for reference)")
        
        # Extract device_id and fp_did if in URL
        print("\n" + "=" * 60)
        print("Device IDs (if you want to update them):")
        print("=" * 60)
        print("Get these from the request URL parameters:")
        print("  - device_id: from ?device_id=...")
        print("  - fp_did: from &fp_did=...")
        print("\nOr leave them as None in config.py to auto-generate")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to parse cookies: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()








