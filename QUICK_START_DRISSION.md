# Quick Start: DrissionPage Auto-Refresh

## ✅ Perfect Solution!

DrissionPage saves your browser session, so you **only login once**!

## 🚀 First Time Setup

1. **Run the test:**
   ```bash
   python test_drission_refresh.py
   ```

2. **Browser opens** - Login to GMGN.ai with your Gmail/account

3. **After login** - Press Enter

4. **Done!** Session is saved to `browser_profile/` folder

## ✨ Subsequent Runs (Fully Automatic!)

After first login, just run:
```bash
python auto_refresh_drission.py
```

Or run the service:
```bash
python cookie_refresh_service_drission.py
```

**No login needed!** Browser uses saved session automatically.

## 📋 How It Works

### First Run:
- ✅ Opens browser (visible)
- ✅ You login once
- ✅ Session saved to `browser_profile/`
- ✅ Cookies extracted

### Every Run After:
- ✅ Opens browser (headless, no window)
- ✅ Uses saved session (already logged in!)
- ✅ Extracts fresh cookies
- ✅ Saves to files
- ✅ **Zero manual intervention!**

## 🎯 Background Service

Run continuously (refreshes every 2 hours):
```bash
python cookie_refresh_service_drission.py
```

- First run: Opens browser for login
- After that: Fully automatic, headless
- Refreshes cookies every 2 hours

## 📁 Files Created

- `browser_profile/` - Your saved browser session (keeps you logged in!)
- `cookies.txt` - Extracted cookies
- `cookies.json` - Cookies in JSON
- `config.py` - Updated automatically

## 💡 Key Benefits

✅ **Login once, reuse forever**  
✅ **No manual cookie copying**  
✅ **Fully automated**  
✅ **Session persists**  
✅ **Works headless after first login**  

## 🔄 Workflow

1. **First time:** Run `test_drission_refresh.py` → Login → Done
2. **Every 2 hours:** Service automatically refreshes cookies
3. **Bot uses cookies:** Automatically from `cookies.txt` or `config.py`

## 🎉 That's It!

You now have **fully automated cookie refresh** with **zero manual login** after the first time!

Perfect for your needs! 🚀








