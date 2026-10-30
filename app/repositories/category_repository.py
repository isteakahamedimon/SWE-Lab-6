from typing import List, Optional
from app.models.category import Category
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)

    def get_by_user(self, user_id: int) -> List[Category]:
        return (
            Category.query.filter_by(user_id=user_id)
            .order_by(Category.name.asc())
            .all()
        )

    def get_by_user_and_type(self, user_id: int, type_: str) -> List[Category]:
        return (
            Category.query.filter_by(user_id=user_id, type=type_)
            .order_by(Category.name.asc())
            .all()
        )

    def get_by_name_and_user(
        self, name: str, user_id: int, type_: Optional[str] = None
    ) -> Optional[Category]:
        query = Category.query.filter(
            Category.user_id == user_id,
            Category.name.ilike(name.strip()),
        )
        if type_:
            query = query.filter_by(type=type_)
        return query.first()

    def create(self, name: str, type_: str, user_id: int, color: str = "#4e73df") -> Category:
        category = Category(
            name=name.strip(),
            type=type_,
            color=color,
            user_id=user_id,
        )
        return self.add(category)
