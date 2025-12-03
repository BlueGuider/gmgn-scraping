# Cookie & Device ID Refresh Guide

## Refresh Frequency

### Cookies
- **`cf_clearance`** - Expires every **2-4 hours** (Cloudflare's bot protection)
- **`__cf_bm`** - Expires every **30 minutes** (Cloudflare bot management)
- **`sid`** - Expires after **session ends** or **24 hours** (GMGN session)
- **`_ga`, `_ga_*`** - Last **2 years** (Google Analytics - rarely need refresh)

**Most Critical:** `cf_clearance` and `__cf_bm` - these are what Cloudflare checks

### Device IDs
- **`device_id`** - Can be **reused indefinitely** (it's just an identifier)
- **`fp_did`** - Can be **reused indefinitely** (fingerprint device ID)

**Good News:** Device IDs don't expire! Once you have working ones, you can keep using them.

## When to Refresh

### You MUST refresh when:
1. Getting **403 Forbidden** errors
2. Getting **"Just a moment..."** Cloudflare challenge pages
3. After **2-4 hours** of bot inactivity
4. When cookies are **older than 4 hours**

### You DON'T need to refresh:
- Device IDs (unless you want to change them)
- Google Analytics cookies (`_ga`)
- If requests are still working fine

## How to Refresh

### Quick Method (Manual)
1. Open GMGN.ai in browser
2. Press **F12** > **Network** tab
3. Make a request (click something on the site)
4. Find any request to `gmgn.ai`
5. Copy the **Cookie** header
6. Update `cookies.txt` or `config.py`

### Automated Method
Use the `refresh_cookies.py` script (see below)

## Automation Options

### Option 1: Browser Extension
- Install a cookie export extension
- Export cookies periodically
- Import into Python script

### Option 2: Selenium (Recommended for Production)
- Automatically visit GMGN.ai
- Extract fresh cookies
- Update config automatically

### Option 3: Manual Refresh Script
- Run a script that reminds you to refresh
- Or use browser DevTools to quickly copy cookies

## Best Practices

1. **Check cookies before important operations**
2. **Set up monitoring** - Alert when 403 errors occur
3. **Use same browser session** - Keep browser open with GMGN.ai
4. **Refresh proactively** - Every 2-3 hours if bot is running continuously

## Testing Cookie Validity

Run this to check if cookies are still valid:
```bash
python quick_test.py
```

If you get 403 errors, cookies need refresh.


