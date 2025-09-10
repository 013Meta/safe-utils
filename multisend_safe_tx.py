#!/usr/bin/env python3
"""
Safe MultiSend Transaction Generator
Combines USDC and ZORA transfers into a single Safe transaction using MultiSend
"""

from web3 import Web3
from eth_utils import keccak
import json
import requests

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
        
        # ERC20 ABI for balanceOf, name, symbol, decimals functions
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
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
    
    def get_token_info(self, token_address):
        """Get token name, symbol, decimals, and balance"""
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            balance = token_contract.functions.balanceOf(self.safe_address).call()
            
            return {
                'address': Web3.to_checksum_address(token_address),
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'balance': balance,
                'balance_formatted': f"{balance / (10 ** decimals):.6f}"
            }
        except Exception as e:
            print(f"❌ Error fetching token info for {token_address}: {e}")
            return None
    
    def discover_tokens_from_list(self, token_list):
        """Check a list of known token addresses for balances"""
        tokens_with_balance = []
        
        print("🔍 Checking tokens for balances...")
        for token_address in token_list:
            token_info = self.get_token_info(token_address)
            if token_info and token_info['balance'] > 0:
                tokens_with_balance.append(token_info)
                print(f"✅ {token_info['symbol']}: {token_info['balance_formatted']}")
        
        return tokens_with_balance
    
    def get_all_tokens_alchemy(self, api_key):
        """Get all ERC20 tokens with balances using Alchemy API"""
        
        # Chain mapping for Alchemy
        chain_names = {
            1: "eth-mainnet",
            10: "opt-mainnet", 
            8453: "base-mainnet",
            42161: "arb-mainnet",
            137: "polygon-mainnet"
        }
        
        chain = chain_names.get(self.chain_id, "eth-mainnet")
        
        url = f"https://{chain}.g.alchemy.com/v2/{api_key}"
        
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenBalances",
            "params": [self.safe_address]  # Gets ALL tokens automatically
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            tokens_with_balance = []
            
            if 'result' in data and 'tokenBalances' in data['result']:
                print(f"🔍 Found {len(data['result']['tokenBalances'])} tokens, checking balances...")
                
                for token_data in data['result']['tokenBalances']:
                    balance = int(token_data['tokenBalance'], 16)  # Convert hex to int
                    if balance > 0:
                        # Get token info (name, symbol, decimals)
                        token_info = self.get_token_info(token_data['contractAddress'])
                        if token_info:
                            tokens_with_balance.append(token_info)
                            print(f"✅ {token_info['symbol']}: {token_info['balance_formatted']}")
            
            return tokens_with_balance
            
        except Exception as e:
            print(f"❌ Error using Alchemy API: {e}")
            print("💡 Falling back to manual token list...")
            return []
        
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
    """Generate MultiSend transaction for ALL tokens in Safe"""
    print("=== Safe MultiSend Transaction Generator (ALL TOKENS) ===\n")
    
    # Configuration - REPLACE WITH YOUR ACTUAL VALUES
    SAFE_ADDRESS = input("Enter your Safe address: ").strip() or "0xYOUR_SAFE_ADDRESS"
    RECIPIENT_ADDRESS = input("Enter recipient address: ").strip() or "0xRECIPIENT_ADDRESS"
    
    if SAFE_ADDRESS == "0xYOUR_SAFE_ADDRESS" or RECIPIENT_ADDRESS == "0xRECIPIENT_ADDRESS":
        print("❌ Please provide actual Safe and recipient addresses!")
        return
    
    # Network selection
    network_input = input("Enter network (1=mainnet, 10=optimism, 8453=base) [default: 1]: ").strip()
    chain_id = int(network_input) if network_input else 1
    
    # Alchemy API key for token discovery
    api_key = input("Enter your Alchemy API key (for token discovery): ").strip()
    
    # RPC endpoint (using Alchemy if API key provided)
    if api_key:
        chain_names = {1: "eth-mainnet", 10: "opt-mainnet", 8453: "base-mainnet"}
        chain_name = chain_names.get(chain_id, "eth-mainnet")
        rpc_url = f"https://{chain_name}.g.alchemy.com/v2/{api_key}"
    else:
        rpc_url = input("Enter RPC URL (or press Enter for default): ").strip()
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
    
    # Create MultiSend transaction builder
    multisend_builder = MultiSendSafeTransaction(SAFE_ADDRESS, chain_id, rpc_url)
    
    print(f"\n🔍 Discovering ALL tokens in Safe {SAFE_ADDRESS}...")
    
    # Discover all tokens with balances
    if api_key:
        all_tokens = multisend_builder.get_all_tokens_alchemy(api_key)
    else:
        print("⚠️  No Alchemy API key provided, checking common tokens only...")
        # Fallback to common token list if no API key
        common_tokens = [
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        ]
        all_tokens = multisend_builder.discover_tokens_from_list(common_tokens)
    
    if not all_tokens:
        print("❌ No tokens with balances found! Check Safe address and connection.")
        return
    
    print(f"\n💰 Found {len(all_tokens)} tokens with balances:")
    for i, token in enumerate(all_tokens, 1):
        print(f"  {i}. {token['symbol']}: {token['balance_formatted']}")
    
    # Ask if user wants to transfer all balances
    transfer_all = input(f"\nTransfer ALL {len(all_tokens)} token balances? (y/n) [default: y]: ").strip().lower()
    
    if transfer_all == 'n':
        print("Select tokens to transfer (comma-separated numbers, e.g., '1,3,5'):")
        selected = input("Token numbers: ").strip()
        if selected:
            try:
                indices = [int(x.strip()) - 1 for x in selected.split(',')]
                all_tokens = [all_tokens[i] for i in indices if 0 <= i < len(all_tokens)]
            except ValueError:
                print("❌ Invalid selection, using all tokens")
    
    # Create token transfers
    token_transfers = []
    for token in all_tokens:
        token_transfers.append((token['address'], RECIPIENT_ADDRESS, token['balance']))
    
    if not token_transfers:
        print("❌ No tokens selected for transfer!")
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
    
    print(f"\n📋 Transaction Details ({len(token_transfers)} tokens):")
    for token_address, recipient, amount in token_transfers:
        # Find token info from our discovered tokens
        token_info = next((t for t in all_tokens if t['address'].lower() == token_address.lower()), None)
        if token_info:
            print(f"  {token_info['symbol']}: {amount / (10 ** token_info['decimals']):.6f}")
    
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
        # Find token info from our discovered tokens
        token_info = next((t for t in all_tokens if t['address'].lower() == token_address.lower()), None)
        if token_info:
            output_data["transfers"].append({
                "token": token_info['symbol'],
                "name": token_info['name'],
                "address": token_address,
                "amount": amount,
                "decimals": token_info['decimals'],
                "amount_formatted": f"{amount / (10 ** token_info['decimals']):.6f}"
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
    print(f"\n💡 This combines ALL {len(token_transfers)} token transfers into a single Safe transaction!")

if __name__ == "__main__":
    main()