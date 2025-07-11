def eth_to_wei(eth_amount):
    """Convert ETH to wei (multiply by 10^18)"""
    eth_amount = str(eth_amount).replace(',', '')
    return int(float(eth_amount) * (10**18))

def eth_to_gwei(eth_amount):
    """Convert ETH to gwei (multiply by 10^9)"""
    eth_amount = str(eth_amount).replace(',', '')
    return int(float(eth_amount) * (10**9))

def gwei_to_wei(gwei_amount):
    """Convert gwei to wei (multiply by 10^9)"""
    gwei_amount = str(gwei_amount).replace(',', '')
    return int(float(gwei_amount) * (10**9))

def main():
    """Main function to handle user input and conversions"""
    print("Ethereum Unit Converter")
    print("======================")
    print("1. ETH to wei")
    print("2. ETH to gwei")
    print("3. gwei to wei")
    
    try:
        choice = input("\nSelect conversion (1-3): ").strip()
        
        if choice == '1':
            amount = input("Enter ETH amount: ")
            result = eth_to_wei(amount)
            print(f"\n{amount} ETH = {result:,} wei")
            print(f"Scientific notation: {result:.2e}")
            
        elif choice == '2':
            amount = input("Enter ETH amount: ")
            result = eth_to_gwei(amount)
            print(f"\n{amount} ETH = {result:,} gwei")
            print(f"Scientific notation: {result:.2e}")
            
        elif choice == '3':
            amount = input("Enter gwei amount: ")
            result = gwei_to_wei(amount)
            print(f"\n{amount} gwei = {result:,} wei")
            print(f"Scientific notation: {result:.2e}")
            
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
            
    except ValueError:
        print("Error: Please enter a valid number")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 