# GMGN API Endpoint Discovery Guide

## Known Working Endpoint

Based on your example, this endpoint works:
```
GET https://gmgn.ai/defi/quotation/v1/rank/bsc/wallets/7d
Query params:
- device_id
- fp_did
- client_id
- from_app=gmgn
- app_ver
- tz_name
- tz_offset
- app_lang=en-US
- os=web
- worker=0
- orderby=pnl_1d (or pnl_7d, pnl_30d)
- direction=desc
```

## How to Discover Other Endpoints

1. **Open GMGN.ai in browser**
2. **Press F12** to open DevTools
3. **Go to Network tab**
4. **Perform the action** you want to replicate (e.g., click button to see first buyers)
5. **Find the API request** in Network tab
6. **Copy the request details:**
   - URL/Endpoint
   - Method (GET/POST)
   - Query parameters
   - Request headers
   - Request body (if POST)

## Expected Endpoint Patterns

Based on common API patterns, these endpoints might exist:

### Token-specific endpoints:
- `/token/{address}/first_buy` - First buy wallets
- `/token/{address}/wallets` - Wallet data for token
- `/token/{address}/hold_time` - Hold time analysis
- `/token/{address}/traders` - Traders for token

### Ranking endpoints:
- `/rank/bsc/wallets/{period}` - Wallet rankings (✅ confirmed working)
- `/rank/bsc/deployers/{period}` - Deployer rankings
- `/rank/bsc/tokens/{period}` - Token rankings

### KOL endpoints:
- `/kol/{name}/profitability` - KOL profitability
- `/kol/{name}/wallets` - KOL wallets

## Testing Strategy

1. **Use test_gmgn.py** to test endpoints
2. **Check response structure** - adjust parsing if needed
3. **If 302 error:**
   - Add cookies from browser
   - Check if endpoint path is correct
   - Verify all required parameters are included

## Common Issues

### Issue: 302 Redirect
**Solution:** Add cookies from browser session

### Issue: 404 Not Found
**Solution:** Endpoint path might be different - check Network tab for actual path

### Issue: Empty response
**Solution:** Check if parameters are correct (period format, address format, etc.)

### Issue: Authentication required
**Solution:** Some endpoints might require login - use cookies from logged-in session

## Next Steps

1. Test the known endpoint (`/rank/bsc/wallets/7d`) - should work
2. Use browser DevTools to find other endpoints
3. Update `gmgn_client.py` with actual endpoint paths
4. Test each command with `test_gmgn.py`
5. Adjust response parsing based on actual API responses



