from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GameHistory(Base):
    __tablename__ = "game_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(String(50), nullable=False)  # Firestore game doc id
    role = Column(String(20), nullable=False)  # "fugitive" | "hunter"
    time_hidden_seconds = Column(Integer, default=0)
    won = Column(Integer, default=0)  # 1 = won, 0 = lost
    played_at = Column(DateTime(timezone=True), server_default=func.now())
