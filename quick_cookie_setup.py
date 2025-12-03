"""
Quick script to set up cookies from browser
Run this and paste your cookie string when prompted
"""
from cookie_helper import parse_cookie_string
import json

def main():
    print("=" * 60)
    print("GMGN Cookie Setup")
    print("=" * 60)
    print("\n1. Open GMGN.ai in your browser")
    print("2. Press F12 > Network tab")
    print("3. Make a request (click something)")
    print("4. Find a request to gmgn.ai")
    print("5. Copy the Cookie header value")
    print("\n" + "=" * 60)
    
    cookie_string = input("\nPaste your cookie string here: ").strip()
    
    if not cookie_string:
        print("❌ No cookie string provided")
        return
    
    try:
        cookies = parse_cookie_string(cookie_string)
        
        print("\n✅ Cookies parsed successfully!")
        print(f"Found {len(cookies)} cookies")
        print("\nCookies:")
        for key in cookies.keys():
            print(f"  - {key}")
        
        # Save to cookies.txt
        with open('cookies.txt', 'w') as f:
            f.write(cookie_string)
        print("\n✅ Saved to cookies.txt")
        
        # Show how to add to config.py
        print("\n" + "=" * 60)
        print("To add to config.py, add this:")
        print("=" * 60)
        print("\nCOOKIES = {")
        for key, value in cookies.items():
            # Truncate long values for display
            display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"    '{key}': '{display_value}',")
        print("}")
        
        # Also save as JSON for easy import
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print("\n✅ Also saved to cookies.json (for reference)")
        
    except Exception as e:
        print(f"\n❌ Error parsing cookies: {e}")

if __name__ == "__main__":
    main()



