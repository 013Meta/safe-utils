#!/usr/bin/env python3
"""
Create approved hash signature format for Safe transactions
"""

def create_approved_hash_signature(owner_address):
    """
    Create the signature format for an owner who called approveHash()
    
    Format: 000000000000000000000000[ADDRESS]000000000000000000000000000000000000000000000000000000000000000001
    
    This tells Safe: "This owner pre-approved the hash, don't check signature"
    """
    # Remove 0x prefix and make lowercase
    clean_address = owner_address.replace('0x', '').lower()
    
    # Pad to 64 characters (32 bytes) with leading zeros
    padded_address = clean_address.zfill(64)
    
    # Create the approved hash signature:
    # - 24 zero bytes (48 chars)
    # - Address (20 bytes = 40 chars) 
    # - 31 zero bytes (62 chars)
    # - 0x01 (1 byte = 2 chars) - indicates "approved hash"
    
    signature = (
        "000000000000000000000000" +  # 12 bytes of zeros
        clean_address +                 # 20 bytes address (40 chars)
        "0000000000000000000000000000000000000000000000000000000000000001"  # 31 zeros + 01
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
        # Single signature
        sig = create_approved_hash_signature(addresses[0])
        result = "0x" + sig
        
        print(f"\n✅ Approved hash signature:")
        print(result)
        
    else:
        # Multiple signatures - need to sort by address
        result = create_multiple_approved_signatures(addresses)
        
        print(f"\n✅ Combined approved hash signatures ({len(addresses)} owners):")
        print(result)
    
    print(f"\nLength: {len(result)} characters")
    print("Use this in execTransaction() signatures parameter")

if __name__ == "__main__":
    main()