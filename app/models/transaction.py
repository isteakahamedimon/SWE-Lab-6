from datetime import datetime, date, timezone
from app.database import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    description = db.Column(db.String(255), default="")
    date = db.Column(db.Date, nullable=False, default=date.today)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.type,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Transaction {self.type} {self.amount} ({self.date})>"
