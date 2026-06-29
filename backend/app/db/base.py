# Import all the models so that Base has them registered before migrating
from app.db.session import Base
from app.models.user import User, UserRole  # noqa
