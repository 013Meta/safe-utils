#!/usr/bin/env python3
"""
Safe Transaction Helper for Token Transfers
Specifically configured for USDC and Zora transfers
"""

from web3 import Web3
from eth_utils import keccak
import json
import sys

# Common token addresses by network
TOKEN_ADDRESSES = {
    "mainnet": {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "ZORA": "0xD8e60e1d0E5373b9f0b73dBD0eb104c55D8B87Cb"  # Replace with actual Zora address
    },
    "optimism": {
        "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        "ZORA": "0x..."  # Add Optimism Zora address if needed
    },
    "base": {
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "ZORA": "0x..."  # Add Base Zora address if needed
    }
}

# Chain IDs
CHAIN_IDS = {
    "mainnet": 1,
    "optimism": 10,
    "base": 8453,
    "arbitrum": 42161,
    "polygon": 137
}

def encode_transfer_data(recipient, amount):
    """Encode ERC20 transfer function data"""
    # Function selector for transfer(address,uint256)
    function_selector = "0xa9059cbb"
    
    # Pad recipient address to 32 bytes
    recipient_padded = Web3.to_checksum_address(recipient)[2:].lower().zfill(64)
    
    # Convert amount to hex and pad to 32 bytes
    amount_hex = hex(amount)[2:].zfill(64)
    
    return function_selector + recipient_padded + amount_hex

def create_safe_tx_data(config):
    """Create Safe transaction data for both transfers"""
    transactions = []
    
    # USDC Transfer
    usdc_data = encode_transfer_data(config['recipient'], config['usdc_amount'])
    usdc_tx = {
        "to": config['usdc_address'],
        "value": "0",
        "data": usdc_data,
        "operation": 0,
        "safeTxGas": "0",
        "baseGas": "0",
        "gasPrice": "0",
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000",
        "nonce": config['starting_nonce']
    }
    
    # Zora Transfer
    zora_data = encode_transfer_data(config['recipient'], config['zora_amount'])
    zora_tx = {
        "to": config['zora_address'],
        "value": "0",
        "data": zora_data,
        "operation": 0,
        "safeTxGas": "0",
        "baseGas": "0",
        "gasPrice": "0",
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000",
        "nonce": config['starting_nonce'] + 1
    }
    
    transactions.append(("USDC", usdc_tx, config['usdc_amount']))
    transactions.append(("Zora", zora_tx, config['zora_amount']))
    
    return transactions

def calculate_tx_hash(safe_address, chain_id, tx_data):
    """Calculate Safe transaction hash"""
    w3 = Web3()
    
    # EIP-712 domain separator components
    domain_typehash = keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
    name_hash = keccak(text="Safe")
    version_hash = keccak(text="1.3.0")
    
    # Calculate domain separator
    domain_separator = keccak(
        w3.codec.encode(
            ['bytes32', 'bytes32', 'bytes32', 'uint256', 'address'],
            [domain_typehash, name_hash, version_hash, chain_id, safe_address]
        )
    )
    
    # Safe transaction type hash
    safe_tx_typehash = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
    
    # Encode transaction
    encoded_tx = w3.codec.encode(
        ['bytes32', 'address', 'uint256', 'bytes32', 'uint8', 'uint256', 'uint256', 'uint256', 'address', 'address', 'uint256'],
        [
            safe_tx_typehash,
            tx_data['to'],
            int(tx_data['value']),
            keccak(hexstr=tx_data['data']),
            tx_data['operation'],
            int(tx_data['safeTxGas']),
            int(tx_data['baseGas']),
            int(tx_data['gasPrice']),
            tx_data['gasToken'],
            tx_data['refundReceiver'],
            tx_data['nonce']
        ]
    )
    
    # Calculate final hash
    safe_tx_hash = keccak(b'\x19\x01' + domain_separator + keccak(encoded_tx))
    
    return "0x" + safe_tx_hash.hex()

def export_transactions(transactions, safe_address, chain_id, output_file=None):
    """Export transaction data to file or console"""
    output_data = {
        "safe_address": safe_address,
        "chain_id": chain_id,
        "transactions": []
    }
    
    for token_name, tx_data, amount in transactions:
        tx_hash = calculate_tx_hash(safe_address, chain_id, tx_data)
        
        tx_info = {
            "token": token_name,
            "amount_wei": str(amount),
            "amount_decimal": f"{amount / (10**6 if token_name == 'USDC' else 10**18):.6f}",
            "transaction_hash": tx_hash,
            "transaction_data": tx_data
        }
        output_data["transactions"].append(tx_info)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"✅ Transaction data exported to {output_file}")
    
    return output_data

def main():
    print("=== Safe Transaction Builder for Token Transfers ===\n")
    
    # Get user inputs
    safe_address = input("Enter your Safe address (or press Enter for example): ").strip()
    if not safe_address:
        safe_address = "0x1234567890123456789012345678901234567890"
        print(f"Using example Safe address: {safe_address}")
    
    recipient = input("Enter recipient address (or press Enter for example): ").strip()
    if not recipient:
        recipient = "0x0987654321098765432109876543210987654321"
        print(f"Using example recipient: {recipient}")
    
    network = input("Enter network (mainnet/optimism/base) [default: mainnet]: ").strip().lower() or "mainnet"
    chain_id = CHAIN_IDS.get(network, 1)
    
    starting_nonce = input("Enter starting nonce for Safe (or press Enter for 0): ").strip()
    starting_nonce = int(starting_nonce) if starting_nonce else 0
    
    # Configuration
    config = {
        "safe_address": Web3.to_checksum_address(safe_address),
        "recipient": Web3.to_checksum_address(recipient),
        "usdc_address": TOKEN_ADDRESSES.get(network, {}).get("USDC", TOKEN_ADDRESSES["mainnet"]["USDC"]),
        "zora_address": TOKEN_ADDRESSES.get(network, {}).get("ZORA", TOKEN_ADDRESSES["mainnet"]["ZORA"]),
        "usdc_amount": 42449330000,  # 42,449.33 USDC
        "zora_amount": 187969927611870000000000,  # 187,969.927611870 ZORA
        "starting_nonce": starting_nonce,
        "chain_id": chain_id
    }
    
    # Create transactions
    transactions = create_safe_tx_data(config)
    
    # Export data
    output_data = export_transactions(transactions, config['safe_address'], chain_id)
    
    # Display results
    print("\n=== Transaction Details ===")
    for tx_info in output_data["transactions"]:
        print(f"\n{tx_info['token']} Transfer:")
        print(f"  Amount: {tx_info['amount_wei']} wei ({tx_info['amount_decimal']} {tx_info['token']})")
        print(f"  Transaction Hash: {tx_info['transaction_hash']}")
        print(f"  To Address: {tx_info['transaction_data']['to']}")
        print(f"  Nonce: {tx_info['transaction_data']['nonce']}")
    
    # Export option
    export_choice = input("\nExport transaction data to file? (y/n): ").strip().lower()
    if export_choice == 'y':
        filename = input("Enter filename (default: safe_transactions.json): ").strip() or "safe_transactions.json"
        export_transactions(transactions, config['safe_address'], chain_id, filename)
    
    print("\n=== Next Steps ===")
    print("1. Use the transaction hashes above to call approveHash on the Safe contract")
    print("2. Collect signatures from other Safe owners")
    print("3. Execute the transaction once threshold is reached")
    print("\n💡 Tip: You can use Etherscan's 'Write Contract' feature to call approveHash")
    print(f"   Safe Contract: {config['safe_address']}")
    print("   Method: approveHash(bytes32 hashToApprove)")

if __name__ == "__main__":
    main() 