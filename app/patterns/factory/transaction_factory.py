from datetime import date
from typing import Dict, Any


class TransactionFactory:
    """
    Factory for producing validated transaction creation payloads
    enforcing business invariants based on transaction type.
    """

    @staticmethod
    def create_payload(
        amount: float,
        type_: str,
        category_id: int,
        user_id: int,
        date_val: date,
        description: str = "",
    ) -> Dict[str, Any]:
        norm_type = type_.lower().strip()
        if norm_type not in ("income", "expense"):
            raise ValueError(f"Invalid transaction type: '{type_}'. Must be 'income' or 'expense'.")

        try:
            val_amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError("Transaction amount must be a valid numeric value.")

        if val_amount <= 0:
            raise ValueError("Transaction amount must be strictly greater than 0.")

        if not isinstance(date_val, date):
            raise ValueError("Valid date object is required.")

        return {
            "amount": round(val_amount, 2),
            "type": norm_type,
            "category_id": int(category_id),
            "user_id": int(user_id),
            "date": date_val,
            "description": description.strip() if description else "",
        }
