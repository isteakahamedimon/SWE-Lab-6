from typing import List, Optional, Tuple
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, category_repo: Optional[CategoryRepository] = None):
        self.category_repo = category_repo or CategoryRepository()

    def get_user_categories(
        self, user_id: int, type_: Optional[str] = None
    ) -> List[Category]:
        if type_:
            return self.category_repo.get_by_user_and_type(user_id, type_)
        return self.category_repo.get_by_user(user_id)

    def get_category_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        cat = self.category_repo.get_by_id(category_id)
        if cat and cat.user_id == user_id:
            return cat
        return None

    def create_category(
        self, name: str, type_: str, user_id: int, color: str = "#4e73df"
    ) -> Tuple[Optional[Category], Optional[str]]:
        name = name.strip()
        type_ = type_.strip().lower()

        if not name:
            return None, "Category name is required."
        if type_ not in ("income", "expense"):
            return None, "Type must be 'income' or 'expense'."

        existing = self.category_repo.get_by_name_and_user(name, user_id, type_)
        if existing:
            return None, f"A {type_} category named '{name}' already exists."

        category = self.category_repo.create(
            name=name, type_=type_, user_id=user_id, color=color or "#4e73df"
        )
        return category, None

    def update_category(
        self, category_id: int, user_id: int, name: str, type_: str, color: str
    ) -> Tuple[Optional[Category], Optional[str]]:
        cat = self.get_category_by_id(category_id, user_id)
        if not cat:
            return None, "Category not found."

        name = name.strip()
        type_ = type_.strip().lower()

        if not name:
            return None, "Category name is required."
        if type_ not in ("income", "expense"):
            return None, "Type must be 'income' or 'expense'."

        existing = self.category_repo.get_by_name_and_user(name, user_id, type_)
        if existing and existing.id != category_id:
            return None, f"Another {type_} category named '{name}' already exists."

        cat.name = name
        cat.type = type_
        cat.color = color or cat.color
        self.category_repo.update(cat)
        return cat, None

    def delete_category(
        self, category_id: int, user_id: int
    ) -> Tuple[bool, Optional[str]]:
        cat = self.get_category_by_id(category_id, user_id)
        if not cat:
            return False, "Category not found."

        # Check if transactions exist under this category
        if cat.transactions.count() > 0:
            return False, "Cannot delete category with associated transactions. Please reassign or delete the transactions first."

        self.category_repo.delete(cat)
        return True, None
