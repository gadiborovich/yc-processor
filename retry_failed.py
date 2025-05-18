import logging
from src.config.config_manager import ConfigManager
from src.storage.models import DatabaseManager, CompanyUrlRecord
from src.scraper.company_scraper import CompanyScraper

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # More detailed logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("retry_scraper")

# Initialize managers
config = ConfigManager()
db = DatabaseManager()
session = db.get_session()

try:
    # Get failed URLs
    failed_urls = session.query(CompanyUrlRecord).filter_by(scrape_status='failed').all()
    failed_url_list = [url.url for url in failed_urls]
    
    print(f"\nRetrying scrape for {len(failed_url_list)} failed companies:")
    for url in failed_url_list:
        print(f"- {url}")
    
    # Create scraper with modified settings
    config_dict = {
        'scraper': {
            'page_load_delay': 5,    # Longer delay between pages
            'max_retries': 5,        # More retries
            'timeout': 60000         # Longer timeout (60 seconds)
        }
    }
    config = ConfigManager(config_dict)
    
    scraper = CompanyScraper(config, db)
    
    # Scrape failed companies
    print("\nStarting scrape...")
    scraper.scrape_companies(failed_url_list)
    
    # Check results
    session.refresh()
    still_failed = session.query(CompanyUrlRecord).filter(
        CompanyUrlRecord.url.in_(failed_url_list),
        CompanyUrlRecord.scrape_status == 'failed'
    ).all()
    
    if still_failed:
        print("\nCompanies that still failed:")
        for url_record in still_failed:
            print(f"- {url_record.url}")
    else:
        print("\nAll companies successfully scraped!")
        
finally:
    session.close() 