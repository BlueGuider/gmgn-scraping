# DrissionPage Setup Guide

## Why DrissionPage?

✅ **Saves browser session** - Login once, reuse forever!  
✅ **No manual login** after first time  
✅ **Automatic cookie extraction**  
✅ **Easier than Selenium** for this use case  

## Installation

```bash
pip install DrissionPage
```

That's it! DrissionPage handles ChromeDriver automatically.

## Quick Start

### First Time (Login Required)

1. **Run the refresh script:**
   ```bash
   python auto_refresh_drission.py
   ```

2. **Browser will open** - Login to GMGN.ai with your Gmail/account

3. **After login** - Press Enter, session will be saved

4. **Done!** - Next time, no login needed!

### Subsequent Runs (Automatic)

After first login, the browser session is saved in `browser_profile/` folder.

Run again:
```bash
python auto_refresh_drission.py
```

This time:
- Browser runs in headless mode (no window)
- Uses saved session (no login needed!)
- Automatically extracts cookies
- Saves to files

### Background Service

Run continuously (refreshes every 2 hours):
```bash
python cookie_refresh_service_drission.py
```

- First run: Browser opens for login
- After that: Runs headless, uses saved session
- Refreshes cookies every 2 hours automatically

## How It Works

1. **First Run:**
   - Opens browser (visible)
   - You login to GMGN.ai
   - Browser session saved to `browser_profile/`
   - Cookies extracted and saved

2. **Subsequent Runs:**
   - Opens browser with saved profile
   - Already logged in (no login needed!)
   - Extracts fresh cookies
   - Saves to files

## Files Created

- `browser_profile/` - Browser session (keeps you logged in)
- `cookies.txt` - Extracted cookies
- `cookies.json` - Cookies in JSON format
- `config.py` - Updated with new cookies

## Benefits Over Selenium

| Feature | Selenium | DrissionPage |
|---------|----------|--------------|
| Session saving | Manual | Automatic |
| Login persistence | No | Yes |
| Setup complexity | High | Low |
| Cookie extraction | Manual | Automatic |

## Troubleshooting

### Browser Profile Issues

If login doesn't persist:
1. Delete `browser_profile/` folder
2. Run again and login fresh

### Login Required Every Time

Check:
- `browser_profile/` folder exists
- Folder has files in it
- Not running in incognito mode

### Cloudflare Challenge

If cookies missing `cf_clearance`:
- Increase `wait_time` to 30-60 seconds
- Run with `headless=False` to see what's happening

## Advanced Usage

### Custom Profile Location

```python
refresher = AutoCookieRefresherDrission(
    user_data_dir=Path('my_custom_profile'),
    headless=True,
    wait_time=20
)
```

### Force Visible Browser

```python
refresher = AutoCookieRefresherDrission(headless=False)
```

## Integration

The bot automatically uses cookies from:
1. `cookies.txt`
2. `config.py`

No need to restart bot - just refresh cookies and bot uses them!

## That's It!

With DrissionPage:
- ✅ Login once
- ✅ Session saved automatically
- ✅ No manual login ever again
- ✅ Fully automated cookie refresh

Perfect for your use case! 🎉








