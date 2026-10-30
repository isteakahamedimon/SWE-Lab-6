from datetime import datetime, timezone
from app.database import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    color = db.Column(db.String(16), default="#4e73df")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    transactions = db.relationship("Transaction", backref="category", lazy="dynamic")
    budgets = db.relationship(
        "Budget", backref="category", cascade="all, delete-orphan", lazy="dynamic"
    )

    __table_args__ = (
        db.UniqueConstraint("name", "type", "user_id", name="uq_category_name_type_user"),
    )

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"
