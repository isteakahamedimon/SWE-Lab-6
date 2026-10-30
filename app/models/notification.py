from datetime import datetime, timezone
from app.database import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(16), default="warning")  # 'info', 'warning', 'danger'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Notification {self.title} ({self.level})>"
