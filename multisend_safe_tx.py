#!/usr/bin/env python3
"""
Safe MultiSend Transaction Generator
Combines USDC and ZORA transfers into a single Safe transaction using MultiSend
"""

from web3 import Web3
from eth_utils import keccak
import json

# MultiSend contract addresses by network
MULTISEND_ADDRESSES = {
    1: "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761",      # Mainnet
    10: "0x998739BFdAAdde7C933B942a68053933098f9EDa",     # Optimism
    8453: "0x998739BFdAAdde7C933B942a68053933098f9EDa",   # Base
    42161: "0x998739BFdAAdde7C933B942a68053933098f9EDa",  # Arbitrum
    137: "0x998739BFdAAdde7C933B942a68053933098f9EDa"     # Polygon
}

class MultiSendSafeTransaction:
    def __init__(self, safe_address, chain_id=1, rpc_url=None):
        if rpc_url:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        else:
            self.w3 = Web3()
        self.safe_address = Web3.to_checksum_address(safe_address)
        self.chain_id = chain_id
        self.multisend_address = MULTISEND_ADDRESSES.get(chain_id, MULTISEND_ADDRESSES[1])
        
        # ERC20 ABI for balanceOf function
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
    
    def get_token_balance(self, token_address):
        """Get ERC20 token balance for the Safe address"""
        try:
            if not self.w3.is_connected():
                print("❌ Web3 not connected to RPC endpoint")
                return 0
                
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            balance = token_contract.functions.balanceOf(self.safe_address).call()
            return balance
        except Exception as e:
            print(f"❌ Error fetching balance for {token_address}: {e}")
            return 0
        
    def encode_transfer_data(self, recipient, amount):
        """Encode ERC20 transfer function data"""
        function_selector = "0xa9059cbb"
        recipient_padded = Web3.to_checksum_address(recipient)[2:].lower().zfill(64)
        amount_hex = hex(amount)[2:].zfill(64)
        return function_selector + recipient_padded + amount_hex
    
    def encode_multisend_transaction(self, to, value, data, operation=0):
        """
        Encode a single transaction for MultiSend
        Format: operation (1 byte) + to (20 bytes) + value (32 bytes) + dataLength (32 bytes) + data
        """
        operation_bytes = operation.to_bytes(1, 'big')
        to_bytes = bytes.fromhex(to[2:])  # Remove 0x prefix
        value_bytes = value.to_bytes(32, 'big')
        data_bytes = bytes.fromhex(data[2:]) if data.startswith('0x') else bytes.fromhex(data)
        data_length_bytes = len(data_bytes).to_bytes(32, 'big')
        
        return operation_bytes + to_bytes + value_bytes + data_length_bytes + data_bytes
    
    def create_multisend_data(self, transactions):
        """
        Create MultiSend transaction data
        transactions: list of (to, value, data, operation) tuples
        """
        encoded_txs = b''
        
        for to, value, data, operation in transactions:
            encoded_tx = self.encode_multisend_transaction(to, value, data, operation)
            encoded_txs += encoded_tx
        
        # MultiSend function selector: multiSend(bytes)
        multisend_selector = "0x8d80ff0a"
        
        # Encode the transactions data
        data_length = len(encoded_txs)
        data_offset = 32  # Offset to the data (after the length)
        
        # ABI encode: selector + offset + length + data
        multisend_data = (
            multisend_selector +
            hex(data_offset)[2:].zfill(64) +  # offset
            hex(data_length)[2:].zfill(64) +  # length
            encoded_txs.hex()                 # actual transaction data
        )
        
        return multisend_data
    
    def calculate_safe_tx_hash(self, safe_tx):
        """Calculate Safe transaction hash for approval"""
        # EIP-712 domain separator
        domain_typehash = keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
        name_hash = keccak(text="Safe")
        version_hash = keccak(text="1.3.0")
        
        domain_separator = keccak(
            self.w3.codec.encode(
                ['bytes32', 'bytes32', 'bytes32', 'uint256', 'address'],
                [domain_typehash, name_hash, version_hash, self.chain_id, self.safe_address]
            )
        )
        
        # Safe transaction type hash
        safe_tx_typehash = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
        
        # Encode transaction
        encoded_tx = self.w3.codec.encode(
            ['bytes32', 'address', 'uint256', 'bytes32', 'uint8', 'uint256', 'uint256', 'uint256', 'address', 'address', 'uint256'],
            [
                safe_tx_typehash,
                safe_tx['to'],
                int(safe_tx['value']),
                keccak(hexstr=safe_tx['data']),
                safe_tx['operation'],
                int(safe_tx['safeTxGas']),
                int(safe_tx['baseGas']),
                int(safe_tx['gasPrice']),
                safe_tx['gasToken'],
                safe_tx['refundReceiver'],
                safe_tx['nonce']
            ]
        )
        
        # Calculate final hash
        safe_tx_hash = keccak(b'\x19\x01' + domain_separator + keccak(encoded_tx))
        return "0x" + safe_tx_hash.hex()
    
    def build_multisend_transaction(self, token_transfers, nonce=0):
        """
        Build a MultiSend transaction for token transfers
        token_transfers: list of (token_address, recipient, amount) tuples
        """
        # Prepare individual transactions for MultiSend
        transactions = []
        
        for token_address, recipient, amount in token_transfers:
            transfer_data = self.encode_transfer_data(recipient, amount)
            transactions.append((
                Web3.to_checksum_address(token_address),
                0,  # value (ETH)
                transfer_data,
                0   # operation (CALL)
            ))
        
        # Create MultiSend data
        multisend_data = self.create_multisend_data(transactions)
        
        # Create Safe transaction
        safe_tx = {
            "to": self.multisend_address,
            "value": "0",
            "data": multisend_data,
            "operation": 1,  # DELEGATECALL for MultiSend
            "safeTxGas": "0",
            "baseGas": "0",
            "gasPrice": "0",
            "gasToken": "0x0000000000000000000000000000000000000000",
            "refundReceiver": "0x0000000000000000000000000000000000000000",
            "nonce": nonce
        }
        
        # Calculate transaction hash
        tx_hash = self.calculate_safe_tx_hash(safe_tx)
        
        return safe_tx, tx_hash

def main():
    """Generate MultiSend transaction for USDC and ZORA transfers"""
    print("=== Safe MultiSend Transaction Generator ===\n")
    
    # Configuration - REPLACE WITH YOUR ACTUAL VALUES
    SAFE_ADDRESS = input("Enter your Safe address: ").strip() or "0xYOUR_SAFE_ADDRESS"
    RECIPIENT_ADDRESS = input("Enter recipient address: ").strip() or "0xRECIPIENT_ADDRESS"
    
    if SAFE_ADDRESS == "0xYOUR_SAFE_ADDRESS" or RECIPIENT_ADDRESS == "0xRECIPIENT_ADDRESS":
        print("❌ Please provide actual Safe and recipient addresses!")
        return
    
    # Network selection
    network_input = input("Enter network (1=mainnet, 10=optimism, 8453=base) [default: 1]: ").strip()
    chain_id = int(network_input) if network_input else 1
    
    # RPC endpoint
    rpc_url = input("Enter RPC URL (or press Enter for default/local): ").strip()
    if not rpc_url:
        if chain_id == 1:
            rpc_url = "https://eth-mainnet.public.blastapi.io"
        elif chain_id == 10:
            rpc_url = "https://optimism-mainnet.public.blastapi.io"
        elif chain_id == 8453:
            rpc_url = "https://base-mainnet.public.blastapi.io"
    
    # Nonce
    nonce_input = input("Enter Safe nonce [default: 0]: ").strip()
    nonce = int(nonce_input) if nonce_input else 0
    
    # Token addresses
    if chain_id == 1:  # Mainnet
        USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        ZORA_ADDRESS = "0xD8e60e1d0E5373b9f0b73dBD0eb104c55D8B87Cb"  # Update with actual
    else:
        print(f"⚠️  Please verify token addresses for chain ID {chain_id}")
        USDC_ADDRESS = input("Enter USDC token address: ").strip()
        ZORA_ADDRESS = input("Enter ZORA token address: ").strip()
    
    # Create MultiSend transaction builder
    multisend_builder = MultiSendSafeTransaction(SAFE_ADDRESS, chain_id, rpc_url)
    
    print(f"\n🔍 Fetching live token balances for Safe {SAFE_ADDRESS}...")
    
    # Get live balances
    usdc_balance = multisend_builder.get_token_balance(USDC_ADDRESS)
    zora_balance = multisend_builder.get_token_balance(ZORA_ADDRESS)
    
    print(f"💰 USDC Balance: {usdc_balance} wei ({usdc_balance / 10**6:.2f} USDC)")
    print(f"💰 ZORA Balance: {zora_balance} wei ({zora_balance / 10**18:.6f} ZORA)")
    
    # Confirm amounts to transfer
    if usdc_balance == 0 and zora_balance == 0:
        print("❌ No token balances found! Check Safe address and RPC connection.")
        return
    
    # Ask if user wants to transfer full balances or specify amounts
    transfer_all = input("\nTransfer all available balances? (y/n) [default: y]: ").strip().lower()
    if transfer_all != 'n':
        USDC_AMOUNT = usdc_balance
        ZORA_AMOUNT = zora_balance
    else:
        if usdc_balance > 0:
            usdc_input = input(f"USDC amount to transfer (max: {usdc_balance / 10**6:.2f}): ").strip()
            USDC_AMOUNT = int(float(usdc_input) * 10**6) if usdc_input else usdc_balance
        else:
            USDC_AMOUNT = 0
            
        if zora_balance > 0:
            zora_input = input(f"ZORA amount to transfer (max: {zora_balance / 10**18:.6f}): ").strip()
            ZORA_AMOUNT = int(float(zora_input) * 10**18) if zora_input else zora_balance  
        else:
            ZORA_AMOUNT = 0
    
    # Define token transfers (only include tokens with balance > 0)
    token_transfers = []
    if USDC_AMOUNT > 0:
        token_transfers.append((USDC_ADDRESS, RECIPIENT_ADDRESS, USDC_AMOUNT))
    if ZORA_AMOUNT > 0:
        token_transfers.append((ZORA_ADDRESS, RECIPIENT_ADDRESS, ZORA_AMOUNT))
    
    if not token_transfers:
        print("❌ No tokens to transfer!")
        return
    
    # Build MultiSend transaction
    safe_tx, tx_hash = multisend_builder.build_multisend_transaction(token_transfers, nonce)
    
    # Display results
    print(f"\n🔄 MultiSend Transaction Generated")
    print(f"Safe Address: {SAFE_ADDRESS}")
    print(f"Recipient: {RECIPIENT_ADDRESS}")
    print(f"Chain ID: {chain_id}")
    print(f"Nonce: {nonce}")
    print(f"MultiSend Contract: {multisend_builder.multisend_address}")
    
    print(f"\n📋 Transaction Details:")
    for token_address, recipient, amount in token_transfers:
        if token_address == USDC_ADDRESS:
            print(f"USDC Transfer: {amount / 10**6:.2f} USDC")
        elif token_address == ZORA_ADDRESS:
            print(f"ZORA Transfer: {amount / 10**18:.6f} ZORA")
    
    print(f"\n🔑 Transaction Hash (for approveHash):")
    print(tx_hash)
    
    print(f"\n📄 Safe Transaction Data:")
    print(json.dumps(safe_tx, indent=2))
    
    # Save to file
    output_data = {
        "config": {
            "safe_address": SAFE_ADDRESS,
            "recipient": RECIPIENT_ADDRESS,
            "chain_id": chain_id,
            "nonce": nonce,
            "multisend_address": multisend_builder.multisend_address
        },
        "transfers": [],
        "transaction_hash": tx_hash,
        "safe_transaction": safe_tx
    }
    
    # Add transfer details to output data
    for token_address, recipient, amount in token_transfers:
        if token_address == USDC_ADDRESS:
            output_data["transfers"].append({
                "token": "USDC", 
                "address": USDC_ADDRESS, 
                "amount": amount, 
                "amount_formatted": f"{amount / 10**6:.2f}"
            })
        elif token_address == ZORA_ADDRESS:
            output_data["transfers"].append({
                "token": "ZORA", 
                "address": ZORA_ADDRESS, 
                "amount": amount, 
                "amount_formatted": f"{amount / 10**18:.6f}"
            })
    
    with open('multisend_safe_tx.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Transaction data saved to: multisend_safe_tx.json")
    
    print(f"\n📖 Next Steps:")
    print("1. Copy the transaction hash above")
    print("2. Go to your Safe contract on Etherscan")
    print("3. Use 'Write Contract' → 'approveHash' function")
    print("4. Paste the transaction hash")
    print("5. Execute the approval")
    print("6. Once threshold is reached, execute the transaction")
    print("\n💡 This combines both token transfers into a single Safe transaction!")

if __name__ == "__main__":
    main()