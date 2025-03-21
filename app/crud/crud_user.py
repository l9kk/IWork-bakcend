from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            is_active=obj_in.is_active,
            is_admin=obj_in.is_admin,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_admin(self, user: User) -> bool:
        return user.is_admin

    def verify_email(self, db: Session, *, user_id: int) -> User:
        user = self.get(db, id=user_id)
        if user:
            user.is_verified = True
            user.verification_token = None
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def set_verification_token(
            self, db: Session, *, user_id: int, token: str
    ) -> User:
        user = self.get(db, id=user_id)
        if user:
            user.verification_token = token
            user.verification_sent_at = datetime.now(timezone.utc)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def set_password_reset_token(
            self, db: Session, *, user_id: int, token: str
    ) -> User:
        user = self.get(db, id=user_id)
        if user:
            user.password_reset_token = token
            user.password_reset_at = datetime.now(timezone.utc)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def reset_password(
            self, db: Session, *, user_id: int, new_password: str
    ) -> User:
        user = self.get(db, id=user_id)
        if user:
            hashed_password = get_password_hash(new_password)
            user.hashed_password = hashed_password
            user.password_reset_token = None
            user.password_reset_at = None
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

user = CRUDUser(User)