from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class CompanyUrlRecord(Base):
    """
    Model for storing company URL records found in the YC directory.
    """
    __tablename__ = "company_urls"
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255), unique=True, nullable=False)
    batch = Column(String(10), nullable=False)
    discovery_date = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime, nullable=True)
    scrape_status = Column(String(50), default="pending")  # pending, completed, failed
    notion_page_id = Column(String(255), nullable=True)
    
    # Relationship to CompanyData
    company_data = relationship("CompanyData", back_populates="url_record", uselist=False)
    
    def __repr__(self):
        return f"<CompanyUrlRecord(url='{self.url}', batch='{self.batch}', status='{self.scrape_status}')>"


class CompanyData(Base):
    """
    Model for storing detailed company data scraped from individual YC company pages.
    """
    __tablename__ = "company_data"
    
    id = Column(Integer, primary_key=True)
    url_record_id = Column(Integer, ForeignKey("company_urls.id"), nullable=False)
    
    # Basic company information
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    yc_website = Column(String(255), nullable=False)  # Same as url in CompanyUrlRecord
    company_website = Column(String(255), nullable=True)
    
    # LinkedIn URLs stored as comma-separated strings
    company_linkedin_urls = Column(Text, nullable=True)  # Comma-separated
    founder_linkedin_urls = Column(Text, nullable=True)  # Comma-separated
    
    # Founder names stored as comma-separated string
    founder_names = Column(Text, nullable=True)  # Comma-separated
    
    # YC batch identifier
    yc_batch = Column(String(10), nullable=False)
    
    # Company launch text for AI analysis
    company_launches = Column(Text, nullable=True)
    
    # Record metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Classification fields
    ai_core_theme = Column(String(100), nullable=True)
    ai_tags = Column(Text, nullable=True)  # Comma-separated
    ai_rationale = Column(Text, nullable=True)
    
    # Relationship to CompanyUrlRecord
    url_record = relationship("CompanyUrlRecord", back_populates="company_data")
    
    def __repr__(self):
        return f"<CompanyData(name='{self.name}', batch='{self.yc_batch}')>"
    
    def get_company_linkedin_url_list(self) -> List[str]:
        """Get company LinkedIn URLs as a list."""
        return self.company_linkedin_urls.split(",") if self.company_linkedin_urls else []
    
    def get_founder_linkedin_url_list(self) -> List[str]:
        """Get founder LinkedIn URLs as a list."""
        return self.founder_linkedin_urls.split(",") if self.founder_linkedin_urls else []
    
    def get_founder_names_list(self) -> List[str]:
        """Get founder names as a list."""
        return self.founder_names.split(",") if self.founder_names else []
    
    def get_ai_tags_list(self) -> List[str]:
        """Get AI tags as a list."""
        return self.ai_tags.split(",") if self.ai_tags else []
    
    def set_company_linkedin_urls(self, urls: List[str]) -> None:
        """Set company LinkedIn URLs from a list."""
        self.company_linkedin_urls = ",".join(urls) if urls else None
    
    def set_founder_linkedin_urls(self, urls: List[str]) -> None:
        """Set founder LinkedIn URLs from a list."""
        self.founder_linkedin_urls = ",".join(urls) if urls else None
    
    def set_founder_names(self, names: List[str]) -> None:
        """Set founder names from a list."""
        self.founder_names = ",".join(names) if names else None
    
    def set_ai_tags(self, tags: List[str]) -> None:
        """Set AI tags from a list."""
        self.ai_tags = ",".join(tags) if tags else None


class DatabaseManager:
    """
    Manager for database operations.
    """
    def __init__(self, db_path: str = "data/yc_companies.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.Session() 