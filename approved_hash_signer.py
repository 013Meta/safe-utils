#!/usr/bin/env python3
"""
Create approved hash signature format for Safe transactions
"""

def create_approved_hash_signature(owner_address):
    """
    Create the signature format for an owner who called approveHash()
    
    Safe pre-validated signature format (65 bytes total):
    - Bytes 0-31: Address that called approveHash() (padded with leading zeros)
    - Bytes 32-63: Padding (all zeros)
    - Byte 64: Signature type (0x01 for pre-validated)
    
    This tells Safe: "This owner pre-approved the hash, don't check signature"
    """
    # Remove 0x prefix and make lowercase
    clean_address = owner_address.replace('0x', '').lower()
    
    # Create the approved hash signature (65 bytes = 130 hex chars):
    # - 12 zero bytes + 20 bytes address = 32 bytes (64 hex chars)
    # - 32 zero bytes = 32 bytes (64 hex chars) 
    # - 0x01 = 1 byte (2 hex chars)
    
    signature = (
        "000000000000000000000000" +  # 12 bytes of leading zeros
        clean_address +                 # 20 bytes address (40 chars)
        "0000000000000000000000000000000000000000000000000000000000000000" +  # 32 zero bytes (64 chars)
        "01"  # signature type: pre-validated
    )
    
    return signature

def create_multiple_approved_signatures(addresses):
    """Create and sort multiple approved hash signatures"""
    signatures = []
    
    # Sort addresses in ascending order (Safe requirement)
    sorted_addresses = sorted([addr.lower() for addr in addresses])
    
    print("Creating approved hash signatures for:")
    for addr in sorted_addresses:
        print(f"  {addr}")
        sig = create_approved_hash_signature(addr)
        signatures.append(sig)
    
    # Combine all signatures
    combined = "0x" + "".join(signatures)
    return combined

def get_signature(owner_address):
    """Simple function to get signature for one address"""
    sig = create_approved_hash_signature(owner_address)
    return "0x" + sig

def main():
    print("=== Safe Approved Hash Signature Creator ===\n")
    
    addresses = []
    print("Enter owner addresses who called approveHash() (empty line to finish):")
    
    while True:
        addr = input("Owner address: ").strip()
        if not addr:
            break
        addresses.append(addr)
    
    if not addresses:
        print("No addresses entered.")
        return
    
    if len(addresses) == 1:
        result = get_signature(addresses[0])
        print(f"\n✅ Approved hash signature:")
        print(result)
    else:
        result = create_multiple_approved_signatures(addresses)
        print(f"\n✅ Combined approved hash signatures ({len(addresses)} owners):")
        print(result)
    
    print(f"\nLength: {len(result)} characters ({(len(result)-2)//2} bytes)")
    expected_bytes = len(addresses) * 65
    if (len(result)-2)//2 == expected_bytes:
        print(f"✅ Correct length: {expected_bytes} bytes ({len(addresses)} × 65 bytes per signature)")
    else:
        print(f"❌ Incorrect length! Expected: {expected_bytes} bytes, Got: {(len(result)-2)//2} bytes")
    
    print("Use this in execTransaction() signatures parameter")

if __name__ == "__main__":
    main()