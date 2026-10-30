from datetime import datetime, timezone
from app.database import db


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM'
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", name="uq_user_category_month"),
    )

    def __repr__(self):
        return f"<Budget {self.month} Cat:{self.category_id} Amt:{self.amount}>"
