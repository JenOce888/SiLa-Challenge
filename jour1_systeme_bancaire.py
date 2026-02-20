import json
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional


class BankAccountError(Exception):
    """Base exception for all bank account errors."""

class InsufficientFundsError(BankAccountError):
    pass

class DepositLimitError(BankAccountError):
    pass

class WithdrawalLimitError(BankAccountError):
    pass

class InvalidAmountError(BankAccountError):
    pass


def _validate_positive(amount: float, label: str = "Amount") -> None:
    if not isinstance(amount, (int, float)):
        raise InvalidAmountError(f"{label} must be a number.")
    if amount <= 0:
        raise InvalidAmountError(f"{label} must be strictly positive, got {amount}.")


_ACCOUNT_REGISTRY: Dict[str, type] = {}

def _register(cls):
    _ACCOUNT_REGISTRY[cls.__name__] = cls
    return cls


class BankAccount:

    def __init__(
        self,
        account_number: str,
        owner_name: str,
        balance: float = 0.0,
    ) -> None:
        if not account_number or not account_number.strip():
            raise ValueError("account_number must be a non-empty string.")
        if not owner_name or not owner_name.strip():
            raise ValueError("owner_name must be a non-empty string.")
        _validate_positive(balance + 1, "Initial balance offset")  # allow 0

        self.account_number: str = account_number.strip()
        self.owner_name: str = owner_name.strip()
        self._balance: float = float(balance)
        self._transaction_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()


    @property
    def balance(self) -> float:
        return self._balance


    def _record(self, **kwargs) -> None:
        """Append a timestamped, uuid-tagged entry to the transaction log."""
        self._transaction_history.append({
            "id": str(uuid.uuid4()),
            "date": datetime.now().isoformat(),
            **kwargs,
        })


    def deposit(self, amount: float) -> None:
        _validate_positive(amount, "Deposit amount")
        with self._lock:
            self._balance += amount
            self._record(type="deposit", amount=amount, balance_after=self._balance)

    def withdraw(self, amount: float) -> None:
        _validate_positive(amount, "Withdrawal amount")
        with self._lock:
            if amount > self._balance:
                raise InsufficientFundsError(
                    f"Cannot withdraw {amount:.2f}: balance is {self._balance:.2f}."
                )
            self._balance -= amount
            self._record(type="withdrawal", amount=amount, balance_after=self._balance)

    def transfer(self, target: "BankAccount", amount: float) -> None:
        """
        Atomic transfer to another account.
        Locks are acquired in a deterministic order to prevent deadlocks.
        """
        _validate_positive(amount, "Transfer amount")
        if target is self:
            raise BankAccountError("Cannot transfer to the same account.")

        # Acquire locks in a consistent order (by id) to avoid deadlocks
        first, second = sorted([self, target], key=lambda a: id(a))
        with first._lock, second._lock:
            if amount > self._balance:
                raise InsufficientFundsError(
                    f"Cannot transfer {amount:.2f}: balance is {self._balance:.2f}."
                )
            self._balance -= amount
            target._balance += amount

            ref = str(uuid.uuid4())
            self._record(type="transfer_out", amount=amount,
                         to=target.account_number, ref=ref,
                         balance_after=self._balance)
            target._record(type="transfer_in", amount=amount,
                           from_=self.account_number, ref=ref,
                           balance_after=target._balance)

    def get_balance(self) -> float:
        return self._balance

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        return list(self._transaction_history)

    def statement(self, n: Optional[int] = None) -> str:
        """Return a human-readable mini-statement of the last *n* transactions."""
        rows = self._transaction_history[-n:] if n else self._transaction_history
        lines = [
            f"Statement for {self.owner_name} ({self.account_number})",
            f"Current balance: {self._balance:.2f}",
            "-" * 48,
        ]
        for tx in rows:
            sign = "-" if "out" in tx["type"] or tx["type"] == "withdrawal" else "+"
            lines.append(
                f"[{tx['date'][:19]}] {tx['type']:<14} "
                f"{sign}{tx['amount']:>10.2f}  "
                f"bal: {tx.get('balance_after', '?'):>10}"
            )
        return "\n".join(lines)


    def _to_dict(self) -> Dict[str, Any]:
        return {
            "account_type": self.__class__.__name__,
            "account_number": self.account_number,
            "owner_name": self.owner_name,
            "balance": self._balance,
            "transaction_history": self._transaction_history,
        }

    def to_json(self) -> str:
        return json.dumps(self._to_dict(), ensure_ascii=False, indent=2)

    def save(self, file: str = "account.json") -> None:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(self._to_dict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls, file: str = "account.json") -> "BankAccount":
        with open(file, encoding="utf-8") as f:
            return cls.from_json(f.read())

    @staticmethod
    def from_json(json_data: str) -> "BankAccount":
        data = json.loads(json_data)
        account_type = data.get("account_type", "BankAccount")
        klass = _ACCOUNT_REGISTRY.get(account_type, BankAccount)
        account = klass.__new__(klass)
        BankAccount.__init__(
            account,
            data["account_number"],
            data["owner_name"],
            data.get("balance", 0.0),
        )
        account._transaction_history = data.get("transaction_history", [])
        return account

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"number={self.account_number!r}, "
            f"owner={self.owner_name!r}, "
            f"balance={self._balance:.2f})"
        )


@_register
class SaveAccount(BankAccount):
    """Savings account: withdrawals capped per operation."""

    WITHDRAWAL_LIMIT: float = 5_000.0

    def withdraw(self, amount: float) -> None:
        _validate_positive(amount, "Withdrawal amount")
        if amount > self.WITHDRAWAL_LIMIT:
            raise WithdrawalLimitError(
                f"SaveAccount withdrawal cap is {self.WITHDRAWAL_LIMIT:.2f} "
                f"(requested {amount:.2f})."
            )
        super().withdraw(amount)


@_register
class ProAccount(BankAccount):
    """Professional account: deposit ceiling + overdraft facility."""

    DEPOSIT_CEILING: float = 1_000_000.0
    OVERDRAFT_LIMIT: float = -50_000.0

    def deposit(self, amount: float) -> None:
        _validate_positive(amount, "Deposit amount")
        if amount > self.DEPOSIT_CEILING:
            raise DepositLimitError(
                f"ProAccount deposit ceiling is {self.DEPOSIT_CEILING:.2f} "
                f"(requested {amount:.2f})."
            )
        super().deposit(amount)

    def withdraw(self, amount: float) -> None:
        _validate_positive(amount, "Withdrawal amount")
        with self._lock:
            if self._balance - amount < self.OVERDRAFT_LIMIT:
                raise InsufficientFundsError(
                    f"ProAccount overdraft limit is {self.OVERDRAFT_LIMIT:.2f} "
                    f"(would reach {self._balance - amount:.2f})."
                )
            self._balance -= amount
            self._record(type="withdrawal", amount=amount, balance_after=self._balance)


# Auto-register the base class too
_ACCOUNT_REGISTRY["BankAccount"] = BankAccount
