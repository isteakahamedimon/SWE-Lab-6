from typing import List
from app.database import db
from app.models.notification import Notification
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self):
        super().__init__(Notification)

    def get_by_user(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()

    def mark_all_as_read(self, user_id: int) -> None:
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()

    def create(
        self, user_id: int, title: str, message: str, level: str = "warning"
    ) -> Notification:
        notif = Notification(
            user_id=user_id, title=title, message=message, level=level
        )
        return self.add(notif)
