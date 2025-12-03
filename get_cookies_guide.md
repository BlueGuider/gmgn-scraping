# How to Get Cookies from Browser (Fix 403 Errors)

## Quick Steps

1. **Open GMGN.ai in your browser** (Chrome/Edge recommended)
2. **Press F12** to open Developer Tools
3. **Go to the "Network" tab**
4. **Navigate to any page on GMGN.ai** (or click a button that makes an API call)
5. **Find a request** to `gmgn.ai` in the Network tab
6. **Click on the request** to see details
7. **Scroll down to "Request Headers"** section
8. **Find the "Cookie:" header** - it will look like:
   ```
   Cookie: _ga=GA1.1.1733557038.1754106388; sid=gmgn%7Cd100ef21e6c5fd9e635a492164310750; cf_clearance=...; __cf_bm=...
   ```
9. **Copy the ENTIRE cookie string** (everything after "Cookie: ")

## Using the Cookies

### Option 1: Update test_gmgn.py directly

Edit `test_gmgn.py` and add your cookies:

```python
from cookie_helper import parse_cookie_string

# Paste your cookie string here
COOKIE_STRING = "your_cookie_string_here"

# Parse and use
cookies = parse_cookie_string(COOKIE_STRING)
client = GMGNClient(cookies=cookies)
```

### Option 2: Create a cookies.txt file

1. Create `cookies.txt` with your cookie string:
   ```
   _ga=GA1.1.1733557038.1754106388; sid=gmgn%7Cd100ef21e6c5fd9e635a492164310750; cf_clearance=...; __cf_bm=...
   ```

2. Update `test_gmgn.py` to load from file:
   ```python
   with open('cookies.txt', 'r') as f:
       cookie_string = f.read().strip()
   cookies = parse_cookie_string(cookie_string)
   client = GMGNClient(cookies=cookies)
   ```

### Option 3: Update config.py

Add cookies to your config:

```python
# In config.py
COOKIES = {
    '_ga': 'GA1.1.1733557038.1754106388',
    'sid': 'gmgn%7Cd100ef21e6c5fd9e635a492164310750',
    'cf_clearance': '...',
    '__cf_bm': '...',
    # ... add all cookies
}
```

Then in your code:
```python
from config import COOKIES
client = GMGNClient(cookies=COOKIES)
```

## Important Cookies

These cookies are especially important:
- **`cf_clearance`** - Cloudflare clearance cookie (most important!)
- **`__cf_bm`** - Cloudflare bot management cookie
- **`sid`** - Session ID

## Notes

- Cookies expire! You may need to refresh them periodically
- `cf_clearance` is generated after passing Cloudflare challenge
- Make sure you're logged into GMGN.ai when copying cookies (if login is required)
- Cookies are browser-specific, so use the same browser you're testing with



