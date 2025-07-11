from web3 import Web3
from eth_account.messages import encode_defunct
from eth_utils import keccak
import json

# ERC20 ABI for transfer function
ERC20_ABI = json.loads('[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]')

class SafeTransactionBuilder:
    def __init__(self, safe_address, chain_id=1):
        """
        Initialize the Safe transaction builder
        
        Args:
            safe_address: The Safe multisig contract address
            chain_id: Chain ID (1 for mainnet, 10 for Optimism, 8453 for Base, etc.)
        """
        self.w3 = Web3()
        self.safe_address = Web3.to_checksum_address(safe_address)
        self.chain_id = chain_id
        
    def encode_erc20_transfer(self, token_address, recipient, amount):
        """
        Encode ERC20 transfer function call
        
        Args:
            token_address: ERC20 token contract address
            recipient: Recipient address
            amount: Amount in smallest unit (wei)
            
        Returns:
            Encoded function call data
        """
        token_address = Web3.to_checksum_address(token_address)
        recipient = Web3.to_checksum_address(recipient)
        
        # Create contract instance
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Encode the transfer function
        data = contract.functions.transfer(recipient, amount).build_transaction()['data']
        
        return data
    
    def create_safe_transaction(self, to, value, data, operation=0, nonce=None):
        """
        Create a Safe transaction structure
        
        Args:
            to: Destination address
            value: ETH value to send (0 for token transfers)
            data: Transaction data
            operation: 0 for call, 1 for delegatecall
            nonce: Transaction nonce (optional)
            
        Returns:
            Safe transaction dictionary
        """
        return {
            "to": Web3.to_checksum_address(to),
            "value": str(value),
            "data": data,
            "operation": operation,
            "safeTxGas": "0",
            "baseGas": "0",
            "gasPrice": "0",
            "gasToken": "0x0000000000000000000000000000000000000000",
            "refundReceiver": "0x0000000000000000000000000000000000000000",
            "nonce": nonce if nonce is not None else 0
        }
    
    def calculate_safe_tx_hash(self, safe_tx):
        """
        Calculate the Safe transaction hash for approval
        
        Args:
            safe_tx: Safe transaction dictionary
            
        Returns:
            Transaction hash (bytes32)
        """
        # EIP-712 domain separator
        domain_separator = keccak(
            self.w3.codec.encode(
                ['bytes32', 'bytes32', 'uint256', 'address'],
                [
                    keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                    keccak(text="Safe"),
                    keccak(text="1.3.0"),
                    self.chain_id,
                    self.safe_address
                ]
            )
        )
        
        # Safe transaction type hash
        safe_tx_typehash = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
        
        # Encode transaction data
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
        safe_tx_hash = keccak(
            b'\x19\x01' + domain_separator + keccak(encoded_tx)
        )
        
        return safe_tx_hash
    
    def build_token_transfer(self, token_address, recipient, amount, nonce=None):
        """
        Build a complete Safe transaction for token transfer
        
        Args:
            token_address: ERC20 token contract address
            recipient: Recipient address
            amount: Amount in smallest unit (wei)
            nonce: Transaction nonce (optional)
            
        Returns:
            Tuple of (safe_tx_dict, tx_hash)
        """
        # Encode transfer data
        data = self.encode_erc20_transfer(token_address, recipient, amount)
        
        # Create Safe transaction
        safe_tx = self.create_safe_transaction(
            to=token_address,
            value=0,
            data=data,
            operation=0,
            nonce=nonce
        )
        
        # Calculate transaction hash
        tx_hash = self.calculate_safe_tx_hash(safe_tx)
        
        return safe_tx, tx_hash


def main():
    """
    Example usage with the provided token values
    """
    # Configuration - REPLACE WITH YOUR ACTUAL VALUES
    SAFE_ADDRESS = "0xYOUR_SAFE_ADDRESS"  # Replace with your Safe address
    RECIPIENT_ADDRESS = "0xRECIPIENT_ADDRESS"  # Replace with recipient address
    
    # Token addresses - REPLACE WITH ACTUAL ADDRESSES
    USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # Mainnet USDC
    ZORA_ADDRESS = "0xD8a8029b4D96581F5b3D0d6E8bD4a7C4bD96319d"  # Replace with actual Zora token address
    
    # Chain ID (1 for mainnet, adjust if using different chain)
    CHAIN_ID = 1
    
    # Token amounts
    USDC_AMOUNT = 42449330000  # 42,449.33 USDC (6 decimals)
    ZORA_AMOUNT = 187969927611870000000000  # 187,969.92761187 ZORA (18 decimals)
    
    # Create builder instance
    builder = SafeTransactionBuilder(SAFE_ADDRESS, CHAIN_ID)
    
    print("=== Safe Transaction Builder ===\n")
    
    # Build USDC transfer
    print("1. USDC Transfer:")
    print(f"   Amount: {USDC_AMOUNT} wei ({USDC_AMOUNT / 10**6:.2f} USDC)")
    usdc_tx, usdc_hash = builder.build_token_transfer(
        USDC_ADDRESS,
        RECIPIENT_ADDRESS,
        USDC_AMOUNT,
        nonce=0  # Set appropriate nonce
    )
    print(f"   Transaction Hash: 0x{usdc_hash.hex()}")
    print(f"   Transaction Data: {json.dumps(usdc_tx, indent=2)}\n")
    
    # Build Zora transfer
    print("2. Zora Transfer:")
    print(f"   Amount: {ZORA_AMOUNT} wei ({ZORA_AMOUNT / 10**18:.6f} ZORA)")
    zora_tx, zora_hash = builder.build_token_transfer(
        ZORA_ADDRESS,
        RECIPIENT_ADDRESS,
        ZORA_AMOUNT,
        nonce=1  # Increment nonce for second transaction
    )
    print(f"   Transaction Hash: 0x{zora_hash.hex()}")
    print(f"   Transaction Data: {json.dumps(zora_tx, indent=2)}\n")
    
    # Instructions for execution
    print("=== Execution Instructions ===")
    print("1. Replace the placeholder addresses with your actual addresses")
    print("2. Verify the token addresses and amounts")
    print("3. Set the correct nonce values for your Safe")
    print("4. Use the transaction hashes to call approveHash on-chain")
    print("5. Once enough signatures are collected, execute the transaction")
    
    # Generate batch transaction data for both transfers
    print("\n=== Batch Transaction (Optional) ===")
    print("If your Safe supports batching, you can execute both transfers in one transaction")
    print("using the MultiSend contract")


if __name__ == "__main__":
    main() 