"""
Indian Number Formatting Utility
Converts numbers to Indian numbering system pronunciation
"""

import re
import logging

logger = logging.getLogger(__name__)

def format_indian_numbers(text):
    """
    Convert Indian numbers to proper pronunciation format
    
    Args:
        text (str): Text containing Indian numbers
        
    Returns:
        str: Text with properly formatted Indian numbers
    """
    try:
        # Pattern to match Indian currency format with commas
        # Examples: ₹1,50,000 or Rs 4,50,000 or 1,50,000
        indian_number_pattern = r'(₹\s*|Rs\.?\s*)?(\d{1,3}(?:,\d{2})*,\d{3})'
        
        def replace_indian_number(match):
            currency_symbol = match.group(1) if match.group(1) else ""
            number_str = match.group(2)
            
            # Remove commas and convert to integer
            number = int(number_str.replace(',', ''))
            
            # Convert to Indian number words
            indian_words = convert_to_indian_words(number)
            
            # Return formatted string
            if currency_symbol:
                return f"{currency_symbol.strip()} {indian_words}"
            else:
                return indian_words
        
        # Replace all Indian number patterns
        formatted_text = re.sub(indian_number_pattern, replace_indian_number, text)
        
        logger.debug(f"Number formatting: '{text}' -> '{formatted_text}'")
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting Indian numbers: {e}")
        return text

def convert_to_indian_words(number):
    """
    Convert a number to Indian number system words
    
    Args:
        number (int): Number to convert
        
    Returns:
        str: Number in Indian words (e.g., "one lakh fifty thousand")
    """
    try:
        if number == 0:
            return "zero"
        
        # Handle negative numbers
        if number < 0:
            return "minus " + convert_to_indian_words(-number)
        
        # Indian number system units
        crore = 10000000  # 1 crore = 10 million
        lakh = 100000     # 1 lakh = 100 thousand
        thousand = 1000   # 1 thousand
        hundred = 100     # 1 hundred
        
        parts = []
        
        # Crores
        if number >= crore:
            crore_part = number // crore
            if crore_part == 1:
                parts.append("one crore")
            else:
                parts.append(f"{convert_basic_number(crore_part)} crore")
            number %= crore
        
        # Lakhs
        if number >= lakh:
            lakh_part = number // lakh
            if lakh_part == 1:
                parts.append("one lakh")
            else:
                parts.append(f"{convert_basic_number(lakh_part)} lakh")
            number %= lakh
        
        # Thousands
        if number >= thousand:
            thousand_part = number // thousand
            if thousand_part == 1:
                parts.append("one thousand")
            else:
                parts.append(f"{convert_basic_number(thousand_part)} thousand")
            number %= thousand
        
        # Hundreds
        if number >= hundred:
            hundred_part = number // hundred
            if hundred_part == 1:
                parts.append("one hundred")
            else:
                parts.append(f"{convert_basic_number(hundred_part)} hundred")
            number %= hundred
        
        # Remaining number (1-99)
        if number > 0:
            parts.append(convert_basic_number(number))
        
        return " ".join(parts)
        
    except Exception as e:
        logger.error(f"Error converting number to words: {e}")
        return str(number)

def convert_basic_number(number):
    """
    Convert numbers 1-99 to words
    
    Args:
        number (int): Number between 1-99
        
    Returns:
        str: Number in words
    """
    if number == 0:
        return ""
    
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"]
    
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    if number < 20:
        return ones[number]
    elif number < 100:
        return tens[number // 10] + ("" if number % 10 == 0 else " " + ones[number % 10])
    
    return str(number)

# Test function
if __name__ == "__main__":
    # Test cases
    test_cases = [
        "₹1,50,000",
        "Rs 4,50,000", 
        "₹12,480",
        "1,50,000",
        "₹ 10,000",
        "₹2,00,000",
        "₹1,60,000",
        "₹4,70,000",
        "₹4,30,000",
        "₹1,660",
        "₹10,820"
    ]
    
    print("Testing Indian Number Formatting:")
    for test in test_cases:
        result = format_indian_numbers(test)
        print(f"Input: {test} -> Output: {result}")