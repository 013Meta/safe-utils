#!/usr/bin/env python3
"""
Decode and display the ERC20 transfer contract interactions
"""

# Transaction values
USDC_AMOUNT = 42449330000  # 42,449.33 USDC (6 decimals)
ZORA_AMOUNT = 187969927611870000000000  # 187,969.927611870 ZORA (18 decimals)

def decode_transfer_data(data_hex):
    """Decode ERC20 transfer function data"""
    # Remove 0x prefix if present
    data = data_hex.replace('0x', '')
    
    # Extract components
    function_selector = '0x' + data[:8]
    recipient = '0x' + data[8:72][-40:]  # Last 40 chars after removing padding
    amount_hex = '0x' + data[72:136]
    amount = int(amount_hex, 16)
    
    return {
        'function_selector': function_selector,
        'function_name': 'transfer(address,uint256)',
        'recipient': recipient,
        'amount': amount
    }

def show_contract_interactions():
    """Display the contract interactions being created"""
    
    # Example recipient address
    recipient = "0x1234567890123456789012345678901234567890"
    
    # Function selector for transfer(address,uint256)
    transfer_selector = "0xa9059cbb"
    
    print("=== ERC20 Transfer Contract Interactions ===\n")
    
    # USDC Transfer
    print("1. USDC Transfer Contract Call:")
    print("   Contract: USDC Token (0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)")
    print("   Function: transfer(address recipient, uint256 amount)")
    print("   Parameters:")
    print(f"     - recipient: {recipient}")
    print(f"     - amount: {USDC_AMOUNT} ({USDC_AMOUNT / 10**6:.2f} USDC)")
    
    # Encode USDC data
    usdc_data = transfer_selector + \
                recipient[2:].lower().zfill(64) + \
                hex(USDC_AMOUNT)[2:].zfill(64)
    
    print(f"\n   Encoded Function Data:")
    print(f"   {usdc_data[:10]}...{usdc_data[-8:]}")
    print(f"   Full: 0x{usdc_data}")
    
    # Decode to verify
    decoded_usdc = decode_transfer_data(usdc_data)
    print(f"\n   Decoded:")
    print(f"     Function: {decoded_usdc['function_name']}")
    print(f"     Selector: {decoded_usdc['function_selector']}")
    print(f"     To: {decoded_usdc['recipient']}")
    print(f"     Amount: {decoded_usdc['amount']} wei")
    
    print("\n" + "-"*60 + "\n")
    
    # ZORA Transfer
    print("2. ZORA Transfer Contract Call:")
    print("   Contract: ZORA Token (0xD8e60e1d0E5373b9f0b73dBD0eb104c55D8B87Cb)")
    print("   Function: transfer(address recipient, uint256 amount)")
    print("   Parameters:")
    print(f"     - recipient: {recipient}")
    print(f"     - amount: {ZORA_AMOUNT} ({ZORA_AMOUNT / 10**18:.6f} ZORA)")
    
    # Encode ZORA data
    zora_data = transfer_selector + \
                recipient[2:].lower().zfill(64) + \
                hex(ZORA_AMOUNT)[2:].zfill(64)
    
    print(f"\n   Encoded Function Data:")
    print(f"   {zora_data[:10]}...{zora_data[-8:]}")
    print(f"   Full: 0x{zora_data}")
    
    # Decode to verify
    decoded_zora = decode_transfer_data(zora_data)
    print(f"\n   Decoded:")
    print(f"     Function: {decoded_zora['function_name']}")
    print(f"     Selector: {decoded_zora['function_selector']}")
    print(f"     To: {decoded_zora['recipient']}")
    print(f"     Amount: {decoded_zora['amount']} wei")
    
    print("\n" + "="*60 + "\n")
    
    print("What happens when Safe executes these transactions:\n")
    print("1. Safe calls USDC_CONTRACT.transfer(recipient, 42449330000)")
    print("   → USDC contract transfers 42,449.33 USDC from Safe to recipient")
    print("\n2. Safe calls ZORA_CONTRACT.transfer(recipient, 187969927611870000000000)")
    print("   → ZORA contract transfers 187,969.927612 ZORA from Safe to recipient")
    
    print("\n" + "="*60 + "\n")
    
    print("The Safe transaction structure:")
    print("- 'to': The token contract address (USDC or ZORA)")
    print("- 'value': 0 (no ETH being sent)")
    print("- 'data': The encoded transfer function call")
    print("- 'operation': 0 (CALL operation)")
    
    print("\nThis is exactly how Safe executes ERC20 token transfers!")

if __name__ == "__main__":
    show_contract_interactions() 