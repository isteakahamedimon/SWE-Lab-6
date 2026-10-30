from typing import Optional, Tuple
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository


DEFAULT_CATEGORIES = [
    # Income categories
    ("Salary", "income", "#28a745"),
    ("Freelance", "income", "#20c997"),
    ("Investments", "income", "#17a2b8"),
    ("Other Income", "income", "#6c757d"),
    # Expense categories
    ("Food & Groceries", "expense", "#fd7e14"),
    ("Housing & Rent", "expense", "#e83e8c"),
    ("Utilities & Bills", "expense", "#6f42c1"),
    ("Transportation", "expense", "#007bff"),
    ("Entertainment & Leisure", "expense", "#ffc107"),
    ("Healthcare", "expense", "#dc3545"),
    ("Shopping", "expense", "#6610f2"),
]


class AuthService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.category_repo = category_repo or CategoryRepository()

    def register_user(
        self, username: str, email: str, password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        username = username.strip()
        email = email.strip().lower()

        if len(username) < 3:
            return None, "Username must be at least 3 characters long."
        if len(password) < 6:
            return None, "Password must be at least 6 characters long."

        if self.user_repo.get_by_username(username):
            return None, "Username already exists."
        if self.user_repo.get_by_email(email):
            return None, "Email address is already registered."

        user = self.user_repo.create(username=username, email=email, password=password)

        # Seed initial default categories for convenient out-of-the-box usage
        for name, type_, color in DEFAULT_CATEGORIES:
            self.category_repo.create(
                name=name, type_=type_, user_id=user.id, color=color
            )

        return user, None

    def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        term = username_or_email.strip()
        user = self.user_repo.get_by_username(term)
        if not user:
            user = self.user_repo.get_by_email(term.lower())

        if user and user.check_password(password):
            return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)
