#!/usr/bin/env python3
"""
Quick Safe Transaction Generator
Outputs transaction hashes and data for USDC and Zora transfers
"""

from web3 import Web3
from eth_utils import keccak
import json

# Your specific values
USDC_AMOUNT = 42449330000  # 42,449.33 USDC (6 decimals)
ZORA_AMOUNT = 187969927611870000000000  # 187,969.927611870 ZORA (18 decimals)

def quick_generate(safe_address, recipient_address, chain_id=1, starting_nonce=0):
    """Generate transaction data quickly"""
    
    # Token addresses (update these for your network)
    USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # Mainnet USDC
    ZORA_ADDRESS = "0xD8e60e1d0E5373b9f0b73dBD0eb104c55D8B87Cb"  # Update with actual Zora address
    
    w3 = Web3()
    
    # Function selector for transfer(address,uint256)
    transfer_selector = "0xa9059cbb"
    
    # Encode USDC transfer
    usdc_data = transfer_selector + \
                Web3.to_checksum_address(recipient_address)[2:].lower().zfill(64) + \
                hex(USDC_AMOUNT)[2:].zfill(64)
    
    # Encode Zora transfer  
    zora_data = transfer_selector + \
                Web3.to_checksum_address(recipient_address)[2:].lower().zfill(64) + \
                hex(ZORA_AMOUNT)[2:].zfill(64)
    
    # Transaction structures
    usdc_tx = {
        "to": Web3.to_checksum_address(USDC_ADDRESS),
        "value": "0",
        "data": usdc_data,
        "operation": 0,
        "safeTxGas": "0",
        "baseGas": "0", 
        "gasPrice": "0",
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000",
        "nonce": starting_nonce
    }
    
    zora_tx = {
        "to": Web3.to_checksum_address(ZORA_ADDRESS),
        "value": "0",
        "data": zora_data,
        "operation": 0,
        "safeTxGas": "0",
        "baseGas": "0",
        "gasPrice": "0", 
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000",
        "nonce": starting_nonce + 1
    }
    
    # Calculate hashes
    def calc_hash(tx):
        # Domain separator
        domain_typehash = keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
        domain_sep = keccak(w3.codec.encode(
            ['bytes32', 'bytes32', 'bytes32', 'uint256', 'address'],
            [domain_typehash, keccak(text="Safe"), keccak(text="1.3.0"), chain_id, safe_address]
        ))
        
        # Transaction hash
        tx_typehash = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
        
        encoded = w3.codec.encode(
            ['bytes32', 'address', 'uint256', 'bytes32', 'uint8', 'uint256', 'uint256', 'uint256', 'address', 'address', 'uint256'],
            [tx_typehash, tx['to'], int(tx['value']), keccak(hexstr=tx['data']), tx['operation'],
             int(tx['safeTxGas']), int(tx['baseGas']), int(tx['gasPrice']), tx['gasToken'], tx['refundReceiver'], tx['nonce']]
        )
        
        return "0x" + keccak(b'\x19\x01' + domain_sep + keccak(encoded)).hex()
    
    usdc_hash = calc_hash(usdc_tx)
    zora_hash = calc_hash(zora_tx)
    
    return {
        "USDC": {
            "hash": usdc_hash,
            "tx": usdc_tx,
            "amount": f"{USDC_AMOUNT / 10**6:.2f} USDC"
        },
        "ZORA": {
            "hash": zora_hash,
            "tx": zora_tx,
            "amount": f"{ZORA_AMOUNT / 10**18:.6f} ZORA"
        }
    }

def main():
    print("=== Safe Transaction Quick Generator ===\n")
    print("⚠️  IMPORTANT: Update the token addresses in the script for your network!\n")
    
    # Replace these with your actual addresses
    SAFE_ADDRESS = "0xYOUR_SAFE_ADDRESS"  # <-- REPLACE THIS
    RECIPIENT_ADDRESS = "0xRECIPIENT_ADDRESS"  # <-- REPLACE THIS
    CHAIN_ID = 1  # 1=mainnet, 10=optimism, 8453=base
    STARTING_NONCE = 0  # Check your Safe's current nonce
    
    if SAFE_ADDRESS == "0xYOUR_SAFE_ADDRESS":
        print("❌ Please edit this script and set your Safe and recipient addresses!")
        print("   Look for SAFE_ADDRESS and RECIPIENT_ADDRESS variables")
        return
    
    result = quick_generate(SAFE_ADDRESS, RECIPIENT_ADDRESS, CHAIN_ID, STARTING_NONCE)
    
    print(f"Safe Address: {SAFE_ADDRESS}")
    print(f"Recipient: {RECIPIENT_ADDRESS}")
    print(f"Chain ID: {CHAIN_ID}")
    print(f"Starting Nonce: {STARTING_NONCE}\n")
    
    print("=" * 60)
    print("TRANSACTION HASHES FOR approveHash():")
    print("=" * 60)
    
    for token, data in result.items():
        print(f"\n{token} Transfer ({data['amount']}):")
        print(f"Hash: {data['hash']}")
        print(f"Nonce: {data['tx']['nonce']}")
    
    print("\n" + "=" * 60)
    print("FULL TRANSACTION DATA:")
    print("=" * 60)
    
    # Save to file
    with open('safe_tx_data.json', 'w') as f:
        json.dump({
            "config": {
                "safe": SAFE_ADDRESS,
                "recipient": RECIPIENT_ADDRESS,
                "chain_id": CHAIN_ID
            },
            "transactions": result
        }, f, indent=2)
    
    print("\n✅ Full transaction data saved to: safe_tx_data.json")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Go to Etherscan and find your Safe contract")
    print("2. Go to 'Write Contract' tab")
    print("3. Find 'approveHash' function")
    print("4. For USDC: paste the USDC hash above")
    print("5. For ZORA: paste the ZORA hash above")
    print("6. Execute both approvals")
    print("7. Once threshold is reached, call execTransaction")

if __name__ == "__main__":
    main() 