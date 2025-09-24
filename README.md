# B2B Recharge Management System

## Project Overview
This project implements a B2B recharge software where multiple sellers can recharge phone numbers using their available credit. Each seller has an account balance, and the system ensures accurate accounting and proper handling of concurrent operations.

### Key Features
- Sellers have individual credit balances.
- Sellers can request credit top-ups, which must be approved by an admin before allocation.
- Sellers can recharge phone numbers via a POST API.
- Seller's balance is automatically reduced according to the recharge amount.
- Seller balances **cannot become negative**.
- Complete logging of all transactions (credit top-ups and sales) to ensure consistency.
- Accurate accounting: sum of all transaction records must match the final seller balance.
- System designed to handle high parallel loads reliably.

### Project Deliverables
1. **Architecture and Model Design**
   - Clear definition of models for sellers, credits, phone numbers, and transaction logs.
   
2. **Credit Top-Up Model**
   - Credit can only be added once per request.
   - Prevents duplicate top-ups by repeated saving.

3. **Transaction Logging**
   - All recharge operations and credit updates must be logged correctly.

4. **Balance Safety**
   - Seller balance cannot go negative during recharge.
   - Seller balance cannot go negative during credit adjustments.

5. **Concurrency and Atomicity**
   - Code must be resistant to race conditions and double-spending.
   - All transfers and updates must be atomic.

6. **Testing**
   - Simple test case with at least two sellers, 10 credit top-ups, and 1,000 recharge operations to verify correct balances.
   - Parallel/concurrent testing to ensure correct accounting under high load.

7. **Python Concurrency Understanding**
   - Clear differentiation between multi-process and multi-threading in Python.

### Example Accounting Check
- Seller account topped up by 1,000,000 IRR.
- Sold 60 recharges of 5,000 IRR each.
- Final balance should be 700,000 IRR.
- All transaction records must match this final balance.

### Notes
- API endpoints should be tested under parallel requests to ensure thread/process safety.
- Emphasis on correct logging and atomic operations to prevent inconsistencies in seller balances.
