from .database import db_manager

def init_database():
    """Initialize database with tables"""
    print("Creating database tables...")
    db_manager.create_tables()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_database()