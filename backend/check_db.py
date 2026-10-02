import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

database_url = os.environ["DATABASE_URL"]
print(f"Подключаемся к: {database_url}")

engine = create_engine(database_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(f"Результат: {result.scalar()}")
    print("Подключение к PostgreSQL работает")