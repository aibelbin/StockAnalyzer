import requests
import json
import time

def get_market_status():
    url = "https://www.nseindia.com/api/marketStatus"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': '*/*',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market status: {e}")
        return None

if __name__ == "__main__":
    status_data = get_market_status()
    if status_data:
        print("Current NSE Market Status:")
        for market in status_data.get('marketState', []):
            print(f"- Market: {market.get('index', market.get('module'))}")
            print(f"  Status: {market.get('marketState')} ({market.get('marketStatusMessage')})")
            if market.get('last'):
                print(f"  Last: {market.get('last')}, Change: {market.get('variation')} ({market.get('percentChange')}%)")
            print("-" * 20)
    
    nifty_status = None
    if status_data:
        for market in status_data.get('marketState', []):
            if market.get('index') == 'NIFTY 50':
                nifty_status = market
                break

    if nifty_status and nifty_status.get('marketState') == 'Closed':
        print("\nNifty 50 market is currently closed. Skipping live data updates.")
    else:
        print("\nNifty 50 market is open or status not explicitly closed. Proceeding with live data updates.")