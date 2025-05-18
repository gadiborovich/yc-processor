import logging
from src.storage.models import DatabaseManager, CompanyUrlRecord

# Get failed URLs
db = DatabaseManager()
session = db.get_session()
failed_urls = session.query(CompanyUrlRecord).filter_by(scrape_status='failed').all()

print("Failed URLs and their last scrape times:")
for url_record in failed_urls:
    print(f"\nURL: {url_record.url}")
    print(f"Last scraped: {url_record.last_scraped}")
    
session.close() 