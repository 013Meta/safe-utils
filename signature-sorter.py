"""
Simple Hash Sorter for Safe Signatures
Just sorts signatures in ascending hex order and concatenates them
"""

def sort_and_concatenate_hashes(hashes):
    """Sort hashes in ascending hex order and concatenate"""
    # Remove 0x prefix for sorting, then sort
    clean_hashes = [h.replace('0x', '').lower() for h in hashes]
    sorted_hashes = sorted(clean_hashes)
    
    print("Sorted hashes:")
    for i, h in enumerate(sorted_hashes, 1):
        print(f"{i}. 0x{h}")
    
    # Concatenate with 0x prefix
    result = "0x" + "".join(sorted_hashes)
    return result

def main():
    print("Safe Transaction Hash Sorter")
    print("=" * 40)
    
    hashes = []
    print("Enter transaction hashes (one per line, empty line to finish):")
    
    while True:
        hash_input = input("Hash: ").strip()
        if not hash_input:
            break
        hashes.append(hash_input)
    
    if hashes:
        result = sort_and_concatenate_hashes(hashes)
        print(f"\n🎯 FINAL SIGNATURE STRING:")
        print(result)
    else:
        print("No hashes entered.")

if __name__ == "__main__":
    main()