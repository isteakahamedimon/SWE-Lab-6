import logging
from app.patterns.observer.subject import TransactionObserver

logger = logging.getLogger("audit")


class AuditLogObserver(TransactionObserver):
    """
    Observer that records audit events whenever transactions are modified.
    Stores events in an internal log list or logger for verification.
    """

    def __init__(self):
        self.audit_log = []

    def on_transaction_event(self, event_type: str, transaction) -> None:
        record = {
            "event": event_type,
            "transaction_id": getattr(transaction, "id", None),
            "amount": getattr(transaction, "amount", None),
            "type": getattr(transaction, "type", None),
            "user_id": getattr(transaction, "user_id", None),
            "date": getattr(transaction, "date", None),
        }
        self.audit_log.append(record)
        logger.info(
            f"AUDIT: Transaction {record['transaction_id']} ({record['type']}) {event_type} by user {record['user_id']}"
        )
