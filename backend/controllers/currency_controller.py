import requests
from utils.config import CURRENCY_API_KEY
import re

def convert_currency(query):
    """
    Takes a query like "convert 50 dollars to rupees" or "convert 50 USD to INR" 
    and fetches real-time currency rates via CurrencyAPI.
    """
    if not CURRENCY_API_KEY:
        return "I cannot convert currency because the Currency API key is missing."
        
    # Helper to map spoken words to currency codes
    code_map = {
        "rupees": "INR", "rupee": "INR", "inr": "INR",
        "dollars": "USD", "dollar": "USD", "usd": "USD", "bucks": "USD",
        "euros": "EUR", "euro": "EUR", "eur": "EUR",
        "pounds": "GBP", "pound": "GBP", "gbp": "GBP",
        "yen": "JPY", "jpy": "JPY"
    }

    words = query.lower().split()
    amount = 1.0
    base = ""
    target = ""
    
    # Very basic parsing string "convert 50 usd to inr"
    try:
        # Extract number
        numbers = [float(s) for s in words if s.replace('.','',1).isdigit()]
        if numbers:
            amount = numbers[0]
            
        # Extract currencies based on dictionary
        found_currencies = [code_map[w] for w in words if w in code_map]
        
        if len(found_currencies) >= 2:
            base = found_currencies[0]
            target = found_currencies[1]
        else:
            return "I couldn't understand which currencies you want to convert."
            
        url = f"https://api.currencyapi.com/v3/latest?apikey={CURRENCY_API_KEY}&base_currency={base}&currencies={target}"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data['data'][target]['value']
            converted = round(amount * rate, 2)
            return f"{amount} {base} is equal to {converted} {target}."
        else:
            return "There was an error reaching the currency server."
            
    except Exception as e:
        print(f"❌ Currency API Error: {e}")
        return "I encountered an error trying to calculate the conversion."

if __name__ == "__main__":
    print(convert_currency("convert 50 dollars to rupees"))
