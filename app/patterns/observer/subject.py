from abc import ABC, abstractmethod
from typing import List, Any


class TransactionObserver(ABC):
    @abstractmethod
    def on_transaction_event(self, event_type: str, transaction: Any) -> None:
        """
        Handles transaction events: 'created', 'updated', 'deleted'
        """
        pass


class TransactionSubject:
    def __init__(self):
        self._observers: List[TransactionObserver] = []

    def attach(self, observer: TransactionObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: TransactionObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_type: str, transaction: Any) -> None:
        for observer in list(self._observers):
            observer.on_transaction_event(event_type, transaction)
