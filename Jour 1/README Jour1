# Day 1 - Secure Banking System
## Objective
Design an object-oriented banking system in Python with:
- Account management (standard, savings, business)
- Custom exceptions
- Timestamped transaction history
- Data persistence in JSON (backup and reload)

## Classes
- BankAccount (Basic account)
- Attributes: number, holder, balance, history
- Methods:  
- SaveAccount (Savings account)
- Inherits from 
- Rule: withdrawal limit set at 5000
- ProAccount (Business Account)
- Inherits from 
- Rules:
- Deposit limit set at 1,000,000
- Overdraft allowed up to –50,000
- Management fees possible on withdrawals/transfers

## Main methods
- adds an amount to the balance
- withdraws an amount with rule checking
- transfer between accounts
- saves in JSON
- serialises to JSON string
- reloads an account from JSON

## Custom exceptions
- InsufficientFundsError -> insufficient balance or overdraft exceeded
- DepositLimitError -> deposit limit exceeded
- WithdrawalLimitError -> withdrawal limit exceeded

