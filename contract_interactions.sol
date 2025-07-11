// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * This file shows the exact contract interactions that the Safe will execute
 * when processing your transactions.
 */

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
}

contract SafeTransactionReference {
    
    // These are the exact function calls that will be executed by the Safe:
    
    // Transaction 1: USDC Transfer
    function executeUSDCTransfer() external {
        IERC20 usdc = IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
        address recipient = address(0); // Replace with your recipient address
        uint256 amount = 42449330000; // 42,449.33 USDC (6 decimals)
        
        // Safe will call:
        usdc.transfer(recipient, amount);
    }
    
    // Transaction 2: ZORA Transfer  
    function executeZORATransfer() external {
        IERC20 zora = IERC20(0xD8E60E1D0E5373B9f0B73dBD0eb104c55d8B87CB); // Update with actual address
        address recipient = address(0); // Replace with your recipient address
        uint256 amount = 187969927611870000000000; // 187,969.927612 ZORA (18 decimals)
        
        // Safe will call:
        zora.transfer(recipient, amount);
    }
    
    /**
     * What the encoded data looks like:
     * 
     * Function selector for transfer(address,uint256): 0xa9059cbb
     * 
     * USDC Transfer Data:
     * 0xa9059cbb
     * 0000000000000000000000[recipient_address_without_0x]
     * 00000000000000000000000000000000000000000000000000000009e22d5f50
     * 
     * ZORA Transfer Data:
     * 0xa9059cbb
     * 0000000000000000000000[recipient_address_without_0x]
     * 00000000000000000000000000000000000000027cddec507a2f92d2c00
     */
} 