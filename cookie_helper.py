"""
Helper script to extract cookies from browser for GMGN scraping
"""
import json

def parse_cookie_string(cookie_string: str) -> dict:
    """
    Parse cookie string from browser into dict format
    
    Example input:
    _ga=GA1.1.1733557038.1754106388; ajs_anonymous_id=%22a88fc42d-9ff0-45d4-a05c-d31903722a3f%22; ...
    
    Returns:
    {
        '_ga': 'GA1.1.1733557038.1754106388',
        'ajs_anonymous_id': '%22a88fc42d-9ff0-45d4-a05c-d31903722a3f%22',
        ...
    }
    """
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def get_cookies_from_browser():
    """
    Instructions for getting cookies from browser
    """
    instructions = """
    How to get cookies from browser:
    
    1. Open GMGN.ai in your browser
    2. Press F12 to open DevTools
    3. Go to Network tab
    4. Make a request (click something on the site)
    5. Find any request to gmgn.ai
    6. Click on it and go to "Headers" section
    7. Scroll down to "Request Headers"
    8. Find the "Cookie:" header
    9. Copy the entire cookie string
    
    Then use parse_cookie_string() to convert it to a dict.
    
    Example:
    cookie_string = "_ga=GA1.1.1733557038.1754106388; sid=gmgn%7Cd100ef21e6c5fd9e635a492164310750; ..."
    cookies = parse_cookie_string(cookie_string)
    
    Then pass cookies to GMGNClient:
    client = GMGNClient(cookies=cookies)
    """
    print(instructions)
    return instructions

if __name__ == "__main__":
    # Example usage
    example_cookie_string = "_ga=GA1.1.1733557038.1754106388; sid=gmgn%7Cd100ef21e6c5fd9e635a492164310750; cf_clearance=BaxZq1iNLF_sOUz3K_hJ08zYovCm8x.0gcBsNvpKb2Q-1764029180-1.2.1.1-b8INgFCii1F69ZU8yTxvfZ3Llvu5iTUfgPNnLjV.69H3aQ3yxlk0U2yl26zL.B86.FG7MkJzidRiYeUD.aWb1JD1AhRQMmsqT._RMeZgxt4o4d6Ui_GMI0Q_LEan3t0gGhffUHiljwgQssNrnNYc7IueKYDE_NHyDpQBKouZXqa6qTKcFxvqcQyx46BjcdP7ifcMEwHqTH5pFVCs6L_hS5.L2F4Lnq5hNDw9mK.oPWs"
    
    print("Example cookie parsing:")
    cookies = parse_cookie_string(example_cookie_string)
    print(json.dumps(cookies, indent=2))
    
    print("\n" + "="*60)
    get_cookies_from_browser()



