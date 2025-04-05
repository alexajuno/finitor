import requests
from typing import Dict, Optional, Union, List
from datetime import datetime

# Exchange rate API endpoint
EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/"

def parse_amount(amount_str: str, currency: str = "VND") -> tuple:
    """
    Parse amount string with currency shortcuts.
    Examples:
        "30k" -> 30000, "VND"
        "1.5m" -> 1500000, "VND"
        "100USD" -> 100, "USD"
        "50EUR" -> 50, "EUR"
        "$100" -> 100, "USD"
        "€50" -> 50, "EUR"
    
    Returns:
        tuple: (amount as float, currency code)
    """
    amount_str = amount_str.strip()
    
    # Check for currency symbols at the beginning
    currency_symbols = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY"
    }
    
    if amount_str and amount_str[0] in currency_symbols:
        currency = currency_symbols[amount_str[0]]
        amount_str = amount_str[1:].strip()
    
    # Check for currency code at the end (3 or 4 uppercase letters)
    import re
    currency_match = re.search(r'([A-Z]{3,4})$', amount_str)
    if currency_match:
        currency = currency_match.group(1)
        amount_str = amount_str[:currency_match.start()].strip()
    
    # Parse amount with Vietnamese Dong shortcuts
    amount_str = amount_str.lower()
    if amount_str.endswith('k'):
        return float(amount_str[:-1]) * 1000, currency
    elif amount_str.endswith('m'):
        return float(amount_str[:-1]) * 1000000, currency
    elif amount_str.endswith('b'):
        return float(amount_str[:-1]) * 1000000000, currency
    else:
        return float(amount_str), currency

def format_amount(amount: float, currency: str = "VND", full: bool = False) -> str:
    """
    Format amount with appropriate suffix based on currency
    
    Parameters:
    amount (float): The amount to format
    currency (str): The currency code
    full (bool): If True, display the full amount without abbreviations
    
    Returns:
    str: The formatted amount
    """
    # Format based on currency
    if currency == "VND":
        if full:
            return f"{amount:,.0f} {currency}"
        
        if amount >= 1000000000:
            return f"{amount/1000000000:.1f}b {currency}"
        elif amount >= 1000000:
            return f"{amount/1000000:.1f}m {currency}"
        elif amount >= 1000:
            return f"{amount/1000:.1f}k {currency}"
        else:
            return f"{amount:,.0f} {currency}"
    elif currency in ["USD", "EUR", "GBP"]:
        # Use standard dollar, euro, pound formatting
        symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"
    else:
        # Default formatting for other currencies
        return f"{amount:,.2f} {currency}"

def get_exchange_rates(base_currency: str = "VND") -> Dict[str, float]:
    """
    Get current exchange rates from external API
    
    Parameters:
    base_currency (str): The base currency code
    
    Returns:
    Dict[str, float]: Dictionary of exchange rates
    """
    try:
        response = requests.get(f"{EXCHANGE_RATE_API}{base_currency}")
        if response.status_code == 200:
            data = response.json()
            return data["rates"]
        else:
            print(f"Error fetching exchange rates: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return {}

def convert_currency(amount: float, from_currency: str, to_currency: str, 
                    exchange_rates: Optional[Dict[str, float]] = None) -> float:
    """
    Convert amount between currencies
    
    Parameters:
    amount (float): The amount to convert
    from_currency (str): Source currency code
    to_currency (str): Target currency code
    exchange_rates (Optional[Dict]): Dictionary of exchange rates (optional)
    
    Returns:
    float: Converted amount
    """
    if from_currency == to_currency:
        return amount
    
    # If no exchange rates provided, fetch them
    if not exchange_rates:
        exchange_rates = get_exchange_rates("USD")  # Use USD as base for consistency
    
    # Get rates for the currencies
    if from_currency in exchange_rates and to_currency in exchange_rates:
        # Convert via the base currency (USD in this case)
        return amount * (exchange_rates[to_currency] / exchange_rates[from_currency])
    else:
        # If currency not found, return original amount
        print(f"Warning: Could not convert from {from_currency} to {to_currency}")
        return amount

def get_common_currencies() -> List[Dict[str, str]]:
    """
    Get a list of common currencies
    
    Returns:
    List[Dict[str, str]]: List of currency objects with code and name
    """
    return [
        {"code": "VND", "name": "Vietnamese Dong"},
        {"code": "USD", "name": "US Dollar"},
        {"code": "EUR", "name": "Euro"},
        {"code": "GBP", "name": "British Pound"},
        {"code": "JPY", "name": "Japanese Yen"},
        {"code": "CNY", "name": "Chinese Yuan"},
        {"code": "SGD", "name": "Singapore Dollar"},
        {"code": "AUD", "name": "Australian Dollar"},
        {"code": "CAD", "name": "Canadian Dollar"},
        {"code": "KRW", "name": "South Korean Won"}
    ] 