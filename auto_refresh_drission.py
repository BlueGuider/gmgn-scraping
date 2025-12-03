"""
Automated cookie refresh using DrissionPage
DrissionPage saves browser sessions, so you only login once!
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
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    print("[ERROR] DrissionPage not installed. Install with: pip install DrissionPage")

from cookie_helper import parse_cookie_string


class AutoCookieRefresherDrission:
    """Automatically refresh cookies using DrissionPage (saves session)"""
    
    def __init__(self, user_data_dir=None, headless=False, wait_time=15):
        """
        Initialize DrissionPage browser
        
        Args:
            user_data_dir: Directory to save browser profile (persists login)
            headless: Run browser in headless mode
            wait_time: Time to wait for Cloudflare challenge
        """
        self.user_data_dir = user_data_dir or Path('browser_profile')
        self.headless = headless
        self.wait_time = wait_time
        self.page = None
    
    def setup_browser(self):
        """Setup Chromium browser with saved profile"""
        if not DRISSION_AVAILABLE:
            return False
        
        try:
            # Configure browser options
            options = ChromiumOptions()
            
            if self.headless:
                options.headless(True)
            
            # Set user data directory to save session
            # This allows browser to remember login!
            user_data_path = str(self.user_data_dir.absolute())
            options.set_user_data_path(user_data_path)
            
            # Additional options to help bypass detection
            options.set_argument('--disable-blink-features=AutomationControlled')
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')
            options.set_argument('--disable-gpu')
            
            # Important: Use random port to avoid conflicts
            import random
            port = random.randint(9223, 9999)
            options.set_argument(f'--remote-debugging-port={port}')
            
            # Create browser page with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.page = ChromiumPage(addr_or_opts=options)
                    
                    # Wait a bit for connection to stabilize
                    time.sleep(2)
                    
                    # Hide webdriver property
                    try:
                        self.page.run_js("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    except:
                        pass  # Ignore if page not ready yet
                    
                    print(f"[OK] Browser started (profile saved to: {user_data_path})")
                    return True
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[WARNING] Attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
                        # Try to clean up any existing browser instances
                        try:
                            if self.page:
                                self.page.quit()
                        except:
                            pass
                    else:
                        raise
            
        except Exception as e:
            print(f"[ERROR] Failed to start browser: {e}")
            print("\nTroubleshooting:")
            print("1. Close any existing Chrome/Chromium browsers")
            print("2. Delete browser_profile folder and try again")
            print("3. Try running with headless=False to see what's happening")
            import traceback
            traceback.print_exc()
            return False
    
    def get_cookies(self, login_if_needed=True):
        """
        Visit GMGN.ai and extract cookies
        
        Args:
            login_if_needed: If True, will wait for manual login on first run
        """
        if not DRISSION_AVAILABLE:
            return None
        
        if not self.page:
            if not self.setup_browser():
                return None
        
        try:
            print("Visiting GMGN.ai...")
            self.page.get('https://gmgn.ai/')
            
            # Check if we need to login
            if login_if_needed:
                # Check for login page or if we're already logged in
                current_url = self.page.url
                page_text = self.page.html if hasattr(self.page, 'html') else ''
                
                if 'login' in current_url.lower() or 'sign in' in page_text.lower():
                    print("\n" + "=" * 60)
                    print("LOGIN REQUIRED")
                    print("=" * 60)
                    print("Please login to GMGN.ai in the browser window")
                    print("After logging in, the session will be saved")
                    print("You won't need to login again!")
                    print("=" * 60)
                    input("\nPress Enter after you've logged in...")
                else:
                    print("[OK] Already logged in (using saved session)")
            
            # Wait for Cloudflare challenge and check if it passes
            print(f"Waiting for Cloudflare challenge to pass (max {self.wait_time}s)...")
            
            # Check for Cloudflare challenge and wait for it to pass
            max_wait = self.wait_time
            waited = 0
            challenge_passed = False
            
            while waited < max_wait:
                time.sleep(2)
                waited += 2
                
                try:
                    current_url = self.page.url
                    page_title = self.page.title if hasattr(self.page, 'title') else ''
                    page_html = self.page.html if hasattr(self.page, 'html') else ''
                    
                    # Check if Cloudflare challenge is still active
                    if "challenges.cloudflare.com" in current_url or "Just a moment" in page_title or "challenge-platform" in page_html:
                        print(f"Cloudflare challenge active... ({waited}/{max_wait}s)")
                        continue
                    else:
                        # Challenge might have passed, check for cf_clearance cookie
                        try:
                            # Quick check for cf_clearance cookie
                            test_cookies = self.page.cookies()
                            has_cf_clearance = False
                            for cookie in test_cookies:
                                name = cookie.get('name') if isinstance(cookie, dict) else (cookie.name if hasattr(cookie, 'name') else None)
                                if name == 'cf_clearance':
                                    has_cf_clearance = True
                                    break
                            
                            if has_cf_clearance or "gmgn.ai" in current_url:
                                print(f"[OK] Cloudflare challenge passed ({waited}s)")
                                challenge_passed = True
                                break
                        except:
                            if "gmgn.ai" in current_url and "challenges" not in current_url:
                                print(f"[OK] Appears to be on GMGN.ai ({waited}s)")
                                challenge_passed = True
                                break
                except:
                    pass
            
            if not challenge_passed:
                print(f"[WARNING] Cloudflare challenge may not have passed after {max_wait}s")
                print("Cookies might be incomplete. Try increasing wait_time.")
            
            # Additional wait to ensure all cookies are set
            print("Waiting for cookies to be fully set...")
            time.sleep(5)
            
            # Navigate to a page that makes API calls (helps establish session and set cookies)
            print("Navigating to trade page to trigger API calls...")
            try:
                self.page.get('https://gmgn.ai/trade/iMPLjKQt?chain=bsc')
                time.sleep(5)  # Wait for API calls to complete
                
                # Try to trigger an API call by interacting with page
                try:
                    # Scroll to trigger lazy loading
                    self.page.scroll.to_bottom()
                    time.sleep(2)
                except:
                    pass
            except Exception as e:
                print(f"[WARNING] Could not navigate to trade page: {e}")
            
            # Wait a bit more for cookies to be set
            time.sleep(3)
            
            # Extract cookies - try multiple methods and domains
            cookies_dict = {}
            try:
                # Method 1: Get ALL cookies from browser using CDP (Chrome DevTools Protocol)
                # This gets cookies from ALL domains, including Cloudflare cookies
                try:
                    browser = None
                    if hasattr(self.page, 'browser'):
                        browser = self.page.browser
                    elif hasattr(self.page, '_browser'):
                        browser = self.page._browser
                    
                    if browser:
                        # Get all cookies via CDP - this gets HttpOnly cookies too!
                        try:
                            # Method 1: getAllCookies (gets ALL cookies from browser)
                            cookies_cdp = browser.run_cdp('Network.getAllCookies')
                            if cookies_cdp and 'cookies' in cookies_cdp:
                                for cookie in cookies_cdp['cookies']:
                                    name = cookie.get('name')
                                    value = cookie.get('value')
                                    domain = cookie.get('domain', '')
                                    
                                    # Get cookies for gmgn.ai domains (including HttpOnly ones)
                                    if 'gmgn.ai' in domain or domain == '' or not domain:
                                        cookies_dict[name] = value
                                
                                print(f"[OK] Got {len(cookies_cdp['cookies'])} total cookies via CDP")
                                print(f"[OK] Filtered to {len(cookies_dict)} gmgn.ai cookies (including HttpOnly)")
                                
                                # Show what we got
                                if cookies_dict:
                                    cookie_names = list(cookies_dict.keys())
                                    print(f"Cookies: {', '.join(cookie_names)}")
                        except Exception as e:
                            print(f"[WARNING] CDP getAllCookies failed: {e}")
                            # Try alternative CDP method
                            try:
                                # Get cookies for specific URLs (this also gets HttpOnly)
                                cookies_cdp = browser.run_cdp('Network.getCookies', {'urls': ['https://gmgn.ai', 'https://*.gmgn.ai']})
                                if cookies_cdp and 'cookies' in cookies_cdp:
                                    for cookie in cookies_cdp['cookies']:
                                        cookies_dict[cookie.get('name')] = cookie.get('value')
                                    print(f"[OK] Got {len(cookies_cdp['cookies'])} cookies via CDP (including HttpOnly)")
                            except Exception as e2:
                                print(f"[WARNING] CDP getCookies also failed: {e2}")
                except Exception as e:
                    print(f"[WARNING] CDP method failed: {e}")
                
                # Method 2: Get cookies for specific domains using DrissionPage
                domains_to_check = ['gmgn.ai', '.gmgn.ai', 'https://gmgn.ai']
                for domain in domains_to_check:
                    try:
                        # Get cookies for this domain
                        domain_cookies = self.page.cookies(domain=domain)
                        if domain_cookies:
                            for cookie in domain_cookies:
                                if isinstance(cookie, dict):
                                    name = cookie.get('name')
                                    value = cookie.get('value')
                                    if name and value:
                                        cookies_dict[name] = value
                                elif hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                                    cookies_dict[cookie.name] = cookie.value
                            print(f"[OK] Got {len(domain_cookies)} cookies for domain: {domain}")
                    except Exception as e:
                        print(f"[WARNING] Failed to get cookies for {domain}: {e}")
                
                # Method 2b: Try getting cookies from all frames/pages
                try:
                    # Get cookies from current page context
                    all_page_cookies = self.page.cookies()
                    if all_page_cookies:
                        for cookie in all_page_cookies:
                            if isinstance(cookie, dict):
                                name = cookie.get('name')
                                value = cookie.get('value')
                                if name and value:
                                    cookies_dict[name] = value
                            elif hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                                cookies_dict[cookie.name] = cookie.value
                        print(f"[OK] Got {len(all_page_cookies)} cookies from page context")
                except Exception as e:
                    print(f"[WARNING] Page context cookies failed: {e}")
                
                # Method 3: Get cookies via JavaScript (current page only)
                try:
                    cookies_str = self.page.run_js('return document.cookie')
                    if cookies_str:
                        js_cookies = parse_cookie_string(cookies_str)
                        cookies_dict.update(js_cookies)
                        print(f"[OK] Got {len(js_cookies)} cookies via JavaScript")
                except Exception as e:
                    print(f"[WARNING] JavaScript method failed: {e}")
                
                # Method 4: Try DrissionPage cookies() method (all cookies)
                try:
                    all_cookies = self.page.cookies()
                    if all_cookies:
                        for cookie in all_cookies:
                            if isinstance(cookie, dict):
                                cookies_dict[cookie.get('name')] = cookie.get('value')
                            elif hasattr(cookie, 'name'):
                                cookies_dict[cookie.name] = cookie.value
                        print(f"[OK] Got cookies via DrissionPage cookies() method")
                except Exception as e:
                    print(f"[WARNING] DrissionPage cookies() failed: {e}")
                
            except Exception as e:
                print(f"[ERROR] Could not get cookies: {e}")
                import traceback
                traceback.print_exc()
            
            if cookies_dict:
                print(f"[SUCCESS] Extracted {len(cookies_dict)} cookies")
                print(f"Cookies found: {', '.join(list(cookies_dict.keys())[:10])}...")
                
                # Check for critical cookies
                critical = ['cf_clearance', '__cf_bm', 'sid']
                missing = [c for c in critical if c not in cookies_dict]
                if missing:
                    print(f"[WARNING] Missing critical cookies: {', '.join(missing)}")
                    print("\nTroubleshooting:")
                    print("1. Cloudflare challenge may not have passed")
                    print("2. Try increasing wait_time (currently {self.wait_time}s)")
                    print("3. Try running with headless=False to see what's happening")
                    print("4. Make sure you're logged into GMGN.ai in the browser")
                else:
                    print("[OK] All critical cookies present!")
                
                return cookies_dict
            else:
                print("[ERROR] No cookies extracted")
                print("Try:")
                print("1. Running with headless=False")
                print("2. Increasing wait_time")
                print("3. Making sure browser can access GMGN.ai")
                return None
            
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
    
    def update_config(self, cookies):
        """Update config.py with new cookies"""
        if not cookies:
            return False
        
        config_path = Path('config.py')
        if not config_path.exists():
            print("[WARNING] config.py not found, skipping config update")
            print("          Create config.py from config.py.example first")
            return False
        
        try:
            # Read current config
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Generate cookies dict string (properly escaped)
            cookies_str = "COOKIES = {\n"
            for key, value in cookies.items():
                # Escape single quotes in values
                escaped_value = value.replace("'", "\\'") if isinstance(value, str) else str(value)
                cookies_str += f"    '{key}': '{escaped_value}',\n"
            cookies_str += "}\n"
            
            # Update or add COOKIES section
            import re
            
            # Pattern to match COOKIES dict (multiline, handles nested quotes and commas)
            # This pattern matches from COOKIES = { to the closing }
            pattern = r'COOKIES\s*=\s*\{[^}]*\}'
            
            if re.search(pattern, config_content, re.DOTALL):
                # Replace existing COOKIES section
                # Use a more robust pattern that handles nested structures
                pattern_detailed = r'COOKIES\s*=\s*\{.*?\n\}'
                config_content = re.sub(pattern_detailed, cookies_str.rstrip(), config_content, flags=re.DOTALL)
                print("[INFO] Replaced existing COOKIES section in config.py")
            else:
                # Add COOKIES section before DEVICE_ID or at end
                if 'DEVICE_ID' in config_content:
                    config_content = config_content.replace('DEVICE_ID', cookies_str + '\nDEVICE_ID')
                    print("[INFO] Added COOKIES section before DEVICE_ID")
                elif 'TELEGRAM_TOKEN' in config_content:
                    # Add after TELEGRAM_TOKEN
                    config_content = config_content.replace(
                        'TELEGRAM_TOKEN',
                        f'TELEGRAM_TOKEN\n\n{cookies_str}'
                    )
                    print("[INFO] Added COOKIES section after TELEGRAM_TOKEN")
                else:
                    config_content += '\n' + cookies_str
                    print("[INFO] Added COOKIES section at end of file")
            
            # Write updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print("[SAVED] Updated config.py with new cookies")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to update config.py: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Close browser (session is saved automatically)"""
        if self.page:
            try:
                # Try graceful shutdown
                self.page.quit()
            except:
                try:
                    # Try closing browser directly
                    if hasattr(self.page, 'browser'):
                        self.page.browser.quit()
                except:
                    pass
            finally:
                self.page = None
                # Give browser time to close
                time.sleep(1)
                print("[OK] Browser closed (session saved)")


def main():
    """Main function"""
    print("=" * 60)
    print("Automated Cookie Refresh with DrissionPage")
    print("=" * 60)
    print("\nBenefits:")
    print("✓ Saves browser session (login once, reuse forever)")
    print("✓ No manual login needed after first time")
    print("✓ Automatically extracts fresh cookies")
    print("\n" + "=" * 60)
    
    if not DRISSION_AVAILABLE:
        print("\n[ERROR] DrissionPage not installed!")
        print("\nInstall with:")
        print("  pip install DrissionPage")
        return
    
    # First run: login required, visible browser
    # Subsequent runs: use saved session, can be headless
    user_data_dir = Path('browser_profile')
    is_first_run = not user_data_dir.exists() or not any(user_data_dir.iterdir())
    
    if is_first_run:
        print("\n[INFO] First run detected - you'll need to login once")
        print("       After this, login will be saved and reused!")
        headless = False
    else:
        print("\n[INFO] Using saved browser session (no login needed)")
        headless = True
    
    refresher = AutoCookieRefresherDrission(
        user_data_dir=user_data_dir,
        headless=headless,
        wait_time=20
    )
    
    try:
        cookies = refresher.get_cookies(login_if_needed=is_first_run)
        
        if cookies:
            refresher.save_cookies(cookies)
            refresher.update_config(cookies)
            print("\n[SUCCESS] Cookies refreshed successfully!")
            if is_first_run:
                print("[INFO] Browser session saved - next run will be automatic!")
        else:
            print("\n[FAILED] Could not extract cookies")
    
    finally:
        refresher.close()


if __name__ == "__main__":
    main()

