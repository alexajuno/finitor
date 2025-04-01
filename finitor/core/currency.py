def parse_amount(amount_str: str) -> float:
    """
    Parse amount string with Vietnamese Dong shortcuts.
    Examples:
        "30k" -> 30000
        "1.5m" -> 1500000
        "2.5k" -> 2500
        "100" -> 100
    """
    amount_str = amount_str.lower().strip()
    
    # Handle suffixes
    if amount_str.endswith('k'):
        return float(amount_str[:-1]) * 1000
    elif amount_str.endswith('m'):
        return float(amount_str[:-1]) * 1000000
    elif amount_str.endswith('b'):
        return float(amount_str[:-1]) * 1000000000
    else:
        return float(amount_str)

def format_amount(amount: float, full: bool = False) -> str:
    """
    Format amount as VND with appropriate suffix
    
    Parameters:
    amount (float): The amount to format
    full (bool): If True, display the full amount without abbreviations
    
    Returns:
    str: The formatted amount
    """
    if full:
        return f"{amount:,.0f} VND"
    
    if amount >= 1000000000:
        return f"{amount/1000000000:.1f}b VND"
    elif amount >= 1000000:
        return f"{amount/1000000:.1f}m VND"
    elif amount >= 1000:
        return f"{amount/1000:.1f}k VND"
    else:
        return f"{amount:,.0f} VND" 