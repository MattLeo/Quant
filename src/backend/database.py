import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

class DatabaseManager:
    def __init__(self, db_path="trading.db"):
        if not os.path.isabs(db_path):
            project_root = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(project_root, db_path)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close the database session"""
        session.close()

db_manager = DatabaseManager()