from decimal import Decimal, getcontext

# Set precision high enough for crypto calculations
getcontext().prec = 50

def transfer_number(result, decimals=6):
    """
    Convert a decimal balance to the smallest unit by multiplying by 10^decimals
    
    Args:
        result: The input number to convert (can be integer or decimal)
        decimals: Number of decimal places (default: 6)
        
    Returns:
        The converted value in smallest units (e.g., wei)
    """
    # Remove commas from the input
    result = str(result).replace(',', '')
    # Use Decimal for precise arithmetic
    decimal_result = Decimal(result)
    multiplier = Decimal(10) ** decimals
    balance = decimal_result * multiplier
    # Convert to integer to remove any fractional parts
    return int(balance)


def main():
    """
    Main function to get user input and display the converted result
    """
    try:
        # Get user input
        number = input("Enter the balance to convert: ")
        
        # Ask for decimal places (optional)
        decimals_input = input("Enter decimal places (press Enter for default 6): ").strip()
        decimals = int(decimals_input) if decimals_input else 6
        
        # Convert and display result
        result = transfer_number(number, decimals)
        
        print(f"\nResult:")
        print(f"Input: {number}")
        print(f"Decimals: {decimals}")
        print(f"Result: {result}")
        
        # Show in scientific notation if very large
        if result >= 1e9:
            print(f"Result (scientific): {result:.2e}")
        
    except ValueError:
        print("Error: Please enter valid numbers")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()