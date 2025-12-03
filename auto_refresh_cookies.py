"""
Automated cookie refresh using Selenium
This script automatically visits GMGN.ai and extracts fresh cookies
"""
import sys
import io
import json
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        # Fallback for older Python
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        USE_WEBDRIVER_MANAGER = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    USE_WEBDRIVER_MANAGER = False
    print("[ERROR] Selenium not installed. Install with: pip install selenium webdriver-manager")

from cookie_helper import parse_cookie_string


class AutoCookieRefresher:
    """Automatically refresh cookies from GMGN.ai"""
    
    def __init__(self, headless=True, wait_time=15):
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Options to help bypass detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        try:
            # Use webdriver-manager if available (auto-downloads ChromeDriver)
            if USE_WEBDRIVER_MANAGER:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            # Execute script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start Chrome: {e}")
            print("\nMake sure:")
            print("1. Chrome browser is installed")
            if not USE_WEBDRIVER_MANAGER:
                print("2. ChromeDriver is installed and in PATH")
                print("3. Or install: pip install webdriver-manager (recommended)")
            return False
    
    def get_cookies(self):
        """Visit GMGN.ai and extract cookies"""
        if not SELENIUM_AVAILABLE:
            return None
        
        if not self.driver:
            if not self.setup_driver():
                return None
        
        try:
            print("Visiting GMGN.ai...")
            self.driver.get('https://gmgn.ai/')
            
            # Wait for page to load and Cloudflare to pass
            print(f"Waiting {self.wait_time} seconds for Cloudflare challenge...")
            time.sleep(self.wait_time)
            
            # Try to detect if Cloudflare challenge is present
            try:
                # Check for Cloudflare challenge page
                if "Just a moment" in self.driver.title or "challenges.cloudflare.com" in self.driver.current_url:
                    print("Cloudflare challenge detected, waiting longer...")
                    time.sleep(10)  # Wait additional time
            except:
                pass
            
            # Make a request to trigger API call (helps establish session)
            try:
                # Try to navigate to a page that makes API calls
                self.driver.get('https://gmgn.ai/trade/iMPLjKQt?chain=bsc')
                time.sleep(5)  # Wait for API calls to complete
            except:
                pass
            
            # Extract cookies
            selenium_cookies = self.driver.get_cookies()
            
            # Convert to dict format
            cookies_dict = {}
            for cookie in selenium_cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            print(f"[SUCCESS] Extracted {len(cookies_dict)} cookies")
            
            # Check for critical cookies
            critical = ['cf_clearance', '__cf_bm', 'sid']
            missing = [c for c in critical if c not in cookies_dict]
            if missing:
                print(f"[WARNING] Missing critical cookies: {', '.join(missing)}")
                print("This might mean Cloudflare challenge wasn't passed")
            else:
                print("[OK] All critical cookies present!")
            
            return cookies_dict
            
        except Exception as e:
            print(f"[ERROR] Failed to get cookies: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_cookies(self, cookies, output_file='cookies.txt'):
        """Save cookies to file"""
        if not cookies:
            return False
        
        # Convert to cookie string format
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        
        # Save to cookies.txt
        with open(output_file, 'w') as f:
            f.write(cookie_string)
        
        # Also save as JSON
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"[SAVED] Cookies saved to {output_file} and cookies.json")
        return True
    
    def update_config(self, cookies, device_id=None, fp_did=None):
        """Update config.py with new cookies"""
        if not cookies:
            return False
        
        config_path = Path('config.py')
        if not config_path.exists():
            print("[WARNING] config.py not found, skipping config update")
            return False
        
        # Read current config
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Generate cookies dict string
        cookies_str = "COOKIES = {\n"
        for key, value in cookies.items():
            cookies_str += f"    '{key}': '{value}',\n"
        cookies_str += "}\n"
        
        # Update or add COOKIES section
        if 'COOKIES = {' in config_content:
            # Find and replace COOKIES section
            import re
            pattern = r'COOKIES = \{.*?\n\}'
            config_content = re.sub(pattern, cookies_str.rstrip(), config_content, flags=re.DOTALL)
        else:
            # Add COOKIES section before DEVICE_ID
            if 'DEVICE_ID' in config_content:
                config_content = config_content.replace('DEVICE_ID', cookies_str + '\nDEVICE_ID')
            else:
                config_content += '\n' + cookies_str
        
        # Write updated config
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print("[SAVED] Updated config.py with new cookies")
        return True
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None


def main():
    """Main function"""
    print("=" * 60)
    print("Automated Cookie Refresh")
    print("=" * 60)
    print("\nThis will:")
    print("1. Open Chrome browser (headless)")
    print("2. Visit GMGN.ai")
    print("3. Wait for Cloudflare challenge to pass")
    print("4. Extract fresh cookies")
    print("5. Save to cookies.txt and config.py")
    print("\n" + "=" * 60)
    
    if not SELENIUM_AVAILABLE:
        print("\n[ERROR] Selenium not installed!")
        print("\nInstall with:")
        print("  pip install selenium")
        print("\nAlso install ChromeDriver:")
        print("  Option 1: Download from https://chromedriver.chromium.org/")
        print("  Option 2: pip install webdriver-manager (auto-downloads)")
        return
    
    refresher = AutoCookieRefresher(headless=True, wait_time=20)
    
    try:
        cookies = refresher.get_cookies()
        
        if cookies:
            refresher.save_cookies(cookies)
            refresher.update_config(cookies)
            print("\n[SUCCESS] Cookies refreshed successfully!")
        else:
            print("\n[FAILED] Could not extract cookies")
            print("Try running with headless=False to see what's happening")
    
    finally:
        refresher.close()


if __name__ == "__main__":
    main()

