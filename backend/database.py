from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Sử dụng SQLite cho đơn giản, file database sẽ được tạo trong thư mục backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/sql_app.db"

# create_engine cần đối số connect_args={"check_same_thread": False} chỉ khi dùng SQLite.
# Điều này là để cho phép nhiều thread tương tác với database.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Mỗi instance của SessionLocal sẽ là một session database mới.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base sẽ được sử dụng để tạo các model ORM (Object Relational Mapper).
Base = declarative_base()

# Dependency để lấy session database trong các endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
