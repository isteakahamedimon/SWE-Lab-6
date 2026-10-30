from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.patterns.factory.transaction_factory import TransactionFactory
from app.patterns.observer.subject import TransactionSubject
from app.patterns.observer.budget_observer import BudgetAlertObserver
from app.patterns.observer.audit_observer import AuditLogObserver
from app.patterns.adapter.csv_adapter import (
    SimpleCSVAdapter,
    BankStatementCSVAdapter,
    CSVExportAdapter,
)


class TransactionService:
    def __init__(
        self,
        transaction_repo: Optional[TransactionRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
        subject: Optional[TransactionSubject] = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository()
        self.category_repo = category_repo or CategoryRepository()
        self.subject = subject or TransactionSubject()

        # Attach default observers if none attached yet
        if not self.subject._observers:
            self.subject.attach(BudgetAlertObserver())
            self.subject.attach(AuditLogObserver())

    def get_transaction_by_id(
        self, transaction_id: int, user_id: int
    ) -> Optional[Transaction]:
        tx = self.transaction_repo.get_by_id(transaction_id)
        if tx and tx.user_id == user_id:
            return tx
        return None

    def get_transactions(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        type_: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> List[Transaction]:
        return self.transaction_repo.filter_transactions(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            type_=type_,
            keyword=keyword,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def create_transaction(
        self,
        amount: float,
        type_: str,
        category_id: int,
        user_id: int,
        date_val: date,
        description: str = "",
    ) -> Tuple[Optional[Transaction], Optional[str]]:
        category = self.category_repo.get_by_id(category_id)
        if not category or category.user_id != user_id:
            return None, "Invalid category selected."

        if category.type != type_.lower().strip():
            return None, f"Category '{category.name}' is for {category.type}s, but transaction type is '{type_}'."

        try:
            payload = TransactionFactory.create_payload(
                amount=amount,
                type_=type_,
                category_id=category_id,
                user_id=user_id,
                date_val=date_val,
                description=description,
            )
        except ValueError as e:
            return None, str(e)

        transaction = self.transaction_repo.create(
            amount=payload["amount"],
            type_=payload["type"],
            category_id=payload["category_id"],
            user_id=payload["user_id"],
            date_=payload["date"],
            description=payload["description"],
        )

        # Notify observers (e.g. BudgetAlertObserver checks spending limits)
        self.subject.notify("created", transaction)

        return transaction, None

    def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        amount: float,
        type_: str,
        category_id: int,
        date_val: date,
        description: str = "",
    ) -> Tuple[Optional[Transaction], Optional[str]]:
        tx = self.get_transaction_by_id(transaction_id, user_id)
        if not tx:
            return None, "Transaction not found."

        category = self.category_repo.get_by_id(category_id)
        if not category or category.user_id != user_id:
            return None, "Invalid category selected."

        if category.type != type_.lower().strip():
            return None, f"Category '{category.name}' is for {category.type}s, but transaction type is '{type_}'."

        try:
            payload = TransactionFactory.create_payload(
                amount=amount,
                type_=type_,
                category_id=category_id,
                user_id=user_id,
                date_val=date_val,
                description=description,
            )
        except ValueError as e:
            return None, str(e)

        tx.amount = payload["amount"]
        tx.type = payload["type"]
        tx.category_id = payload["category_id"]
        tx.date = payload["date"]
        tx.description = payload["description"]

        updated = self.transaction_repo.update(tx)
        self.subject.notify("updated", updated)

        return updated, None

    def delete_transaction(
        self, transaction_id: int, user_id: int
    ) -> Tuple[bool, Optional[str]]:
        tx = self.get_transaction_by_id(transaction_id, user_id)
        if not tx:
            return False, "Transaction not found."

        self.transaction_repo.delete(tx)
        self.subject.notify("deleted", tx)
        return True, None

    def import_transactions(
        self, user_id: int, content: str, adapter_type: str = "simple"
    ) -> Tuple[int, List[str]]:
        """
        Imports transactions using selected Adapter.
        Returns count of imported items and list of error messages if any.
        """
        adapter = (
            BankStatementCSVAdapter()
            if adapter_type == "bank"
            else SimpleCSVAdapter()
        )

        try:
            records = adapter.parse(content)
        except Exception as e:
            return 0, [f"Failed to parse CSV file: {str(e)}"]

        imported_count = 0
        errors = []

        for idx, rec in enumerate(records, start=1):
            cat_name = rec["category_name"]
            t_type = rec["type"]

            # Lookup or auto-create category for user
            cat = self.category_repo.get_by_name_and_user(cat_name, user_id, type_=t_type)
            if not cat:
                cat = self.category_repo.create(
                    name=cat_name, type_=t_type, user_id=user_id
                )

            tx, err = self.create_transaction(
                amount=rec["amount"],
                type_=t_type,
                category_id=cat.id,
                user_id=user_id,
                date_val=rec["date"],
                description=rec["description"],
            )

            if err:
                errors.append(f"Row {idx}: {err}")
            else:
                imported_count += 1

        return imported_count, errors

    def export_transactions_csv(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        type_: Optional[str] = None,
    ) -> str:
        transactions = self.get_transactions(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            type_=type_,
        )
        return CSVExportAdapter.export(transactions)
